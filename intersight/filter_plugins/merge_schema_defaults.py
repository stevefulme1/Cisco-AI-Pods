"""
Ansible filter plugins for cisco.intersight playbooks.

Filters provided:
  merge_schema_defaults(item, schema, definition_key)
      Fills in schema-defined default values for any key the user omitted.

  to_module_params(item, module_name)
      Renames schema model keys to the cisco.intersight module's parameter
      names, expands complex nested structures into flat module params, and
      drops keys the module does not accept (to prevent "Unsupported
      parameters" errors).

Recommended usage (chain both filters before passing to a module):

  vars:
    intersight_schema: "{{ lookup('ansible.builtin.file',
                          playbook_dir ~ '/../schema/cisco-ai-pods.json')
                          | from_json }}"
  tasks:
    - cisco.intersight.intersight_ntp_policy: >-
        {{
          item.1
          | merge_schema_defaults(intersight_schema, 'intersight.ntp')
          | to_module_params('intersight_ntp_policy')
          | combine({'organization': item.0.key, 'state': 'present'})
        }}
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import re
import copy
import ipaddress

# ---------------------------------------------------------------------------
# Schema-to-module key rename tables
# Keys with a None value are dropped (schema-only, no module equivalent).
# ---------------------------------------------------------------------------
_MODULE_KEY_RENAMES = {
    # ---- Pools ----------------------------------------------------------------
    'intersight_ip_pool': {
        'assignment_order': None,
        'ipv4_configuration': 'ipv4_config',
        'ipv6_configuration': 'ipv6_config',
    },
    'intersight_iqn_pool': {
        'assignment_order': None,
        'iqn_blocks': 'iqn_suffix_blocks',
    },
    'intersight_mac_pool': {
        'assignment_order': None,
    },
    'intersight_uuid_pool': {
        'assignment_order': None,
        'uuid_blocks': 'uuid_suffix_blocks',
    },
    'intersight_wwn_pool': {
        'assignment_order': None,
    },
    # ---- Policies (compute) ---------------------------------------------------
    'intersight_boot_order_policy': {
        'boot_mode': 'configured_boot_mode',
        'enable_secure_boot': 'uefi_enable_secure_boot',
    },
    'intersight_firmware_policy': {
        'advanced_mode': None,
        'model_bundle_version': 'model_bundle_combo',
    },
    'intersight_ntp_policy': {
        'enabled': 'enable',
    },
    'intersight_virtual_media_policy': {
        'enable_virtual_media': 'enable',
        'enable_virtual_media_encryption': 'encryption',
        'enable_low_power_usb': 'low_power_usb',
        'add_virtual_media': None,
    },
    'intersight_power_policy': {
        'dynamic_power_rebalancing': None,
        'extended_power_capacity': None,
        'power_allocation': None,
    },
    # ---- Policies (network / fabric) -----------------------------------------
    'intersight_flow_control_policy': {
        'priority': 'priority_flow_control_mode',
        'receive': 'receive_direction',
        'send': 'send_direction',
    },
    'intersight_link_control_policy': {
        'admin_state': 'udld_admin_state',
        'mode': 'udld_mode',
    },
    'intersight_switch_control_policy': {
        'switching_mode_ethernet': 'ethernet_switching_mode',
        'switching_mode_fc': 'fc_switching_mode',
        'vlan_port_count_optimization': 'vlan_port_optimization_enabled',
        'mac_address_table_aging': 'mac_aging_option',
        'fabric_port_channel_vhba_reset': 'fabric_pc_vhba_reset',
        'aes_primary_key': 'primary_key',
        'udld_global_settings': None,
        'target_platform': None,
    },
    'intersight_system_qos_policy': {
        'configure_default_classes': None,
        'configure_recommended_classes': None,
        'jumbo_mtu': None,
    },
    # ---- Policies (ethernet) -----------------------------------------
    'intersight_ethernet_adapter_policy': {
        'enable_vxlan_offload': 'vxlan_enabled',
        'enable_nvgre_offload': 'nvgre_enabled',
        'enable_accelerated_receive_flow_steering': 'arfs_enabled',
        'enable_precision_time_protocol': 'ptp_enabled',
        'enable_advanced_filter': 'advanced_filter',
        'enable_interrupt_scaling': 'interrupt_scaling',
        'enable_geneve_offload': 'geneve_enabled',
        'enable_ether_channel_pinning': 'etherchannel_pinning_enabled',
        'adapter_template': None,
        'receive_side_scaling_enable': 'arfs_enabled',
        # Complex nested objects not directly supported as flat params
        'completion': None,
        'interrupt_settings': None,
        'receive': None,
        'receive_side_scaling': None,
        'transmit': None,
        'roce_settings': None,
        'tcp_offload': None,
        'uplink_failback_timeout': None,
    },
    'intersight_ethernet_network_control_policy': {
        'cdp_enable': 'cdp_enabled',
        'mac_register_mode': 'mac_registration_mode',
        'lldp_enable_receive': 'lldp_receive_enabled',
        'lldp_enable_transmit': 'lldp_transmit_enabled',
        'action_on_uplink_fail': 'uplink_fail_action',
        'mac_security_forge': 'forge_mac',
    },
    'intersight_ethernet_qos_policy': {
        'class_of_service': 'cos',
        'enable_trust_host_cos': 'trust_host_cos',
    },
    'intersight_adapter_config_policy': {
        'add_vic_adapter_configuration': 'settings',
    },
    'intersight_iscsi_adapter_policy': {
        'tcp_connection_timeout': 'connection_time_out',
    },
    'intersight_iscsi_static_target_policy': {
        'ip_address': None,
    },
    'intersight_iscsi_boot_policy': {
        'iscsi_adapter_policy': 'iscsi_adapter_policy_name',
        'primary_target_policy': 'primary_target_policy_name',
        'secondary_target_policy': 'secondary_target_policy_name',
        'initiator_ip_pool': 'initiator_ip_pool_name',
        'dhcp_vendor_id_iqn': 'auto_targetvendor_name',
    },
    'intersight_lan_connectivity_policy': {
        'enable_azure_stack_host_qos': 'azure_qos_enabled',
        'iqn_pool': 'iqn_pool_name',
        'iqn_static_identifier': 'static_iqn_name',
        'vnic_placement_mode': 'placement_mode',
        'vnics': 'vnics',
        'vnics_from_template': None,
    },
    'intersight_san_connectivity_policy': {
        'vhba_placement_mode': 'placement_mode',
        'wwnn_static_address': 'static_wwnn_address',
        'vhbas': 'vhbas',
        'vhbas_from_template': None,
    },
    'intersight_drive_security_policy': {
        'remote_key_management': 'remote_key',
    },
    'intersight_vhba_template': {
        'allow_override': 'enable_override',
        'fc_zone_policies': 'fibre_channel_zone_policy_names',
        'fibre_channel_adapter_policy': 'fibre_channel_adapter_policy_name',
        'fibre_channel_network_policy': 'fibre_channel_network_policy_name',
        'fibre_channel_qos_policy': 'fibre_channel_qos_policy_name',
        'persistent_lun_bindings': 'persistent_bindings',
        'placement_switch_id': 'switch_id',
        'wwpn_pool': 'wwpn_pool_name',
    },
    'intersight_vnic_template': {
        'allow_override': 'enable_override',
        'enable_failover': 'failover_enabled',
        'ethernet_adapter_policy': 'eth_adapter_policy_name',
        'ethernet_network_control_policy': 'fabric_eth_network_control_policy_name',
        'ethernet_network_group_policies': 'fabric_eth_network_group_policy_name',
        'ethernet_qos_policy': 'eth_qos_policy_name',
        'iscsi_boot_policy': 'iscsi_boot_policy_name',
        'mac_address_pool': 'mac_pool_name',
        'placement_switch_id': 'switch_id',
        'sriov': 'sriov_settings',
        'usnic': 'usnic_settings',
        'vmq': 'vmq_settings',
    },
    # ---- Policies (management) -----------------------------------------------
    'intersight_imc_access_policy': {
        'inband_ip_pool': 'ip_pool',
        'inband_vlan_id': 'vlan_id',
        'out_of_band_ip_pool': None,
        'ipv4_address_configuration': None,
        'ipv6_address_configuration': None,
    },
    'intersight_ipmi_over_lan_policy': {
        'encryption_key': None,
    },
    'intersight_local_user_policy': {
        '_expand_password_properties': True,
        'password_properties': None,
        'users': 'local_users',
    },
    'intersight_device_connector_policy': {
        'configuration_from_intersight_only': 'enable_lockout',
    },
    'intersight_network_connectivity_policy': {
        'obtain_ipv4_dns_from_dhcp': 'enable_ipv4_dns_from_dhcp',
        'obtain_ipv6_dns_from_dhcp': 'enable_ipv6_dns_from_dhcp',
        'update_domain': 'dynamic_dns_domain',
        'dns_servers_v4': None,
        'dns_servers_v6': None,
    },
    'intersight_snmp_policy': {
        'enable_snmp': 'enabled',
        'snmp_community_access': 'community_access',
        'snmp_engine_input_id': 'engine_input_id',
        'snmp_trap_destinations': 'snmp_traps',
        'system_contact': 'sys_contact',
        'system_location': 'sys_location',
        'trap_community_string': 'trap_community',
    },
    'intersight_syslog_policy': {
        'local_logging': None,
        'remote_logging': None,
    },
    'intersight_kvm_policy': {
        'enable_virtual_kvm': 'enabled',
        'allow_tunneled_vkvm': 'tunneled_kvm_enabled',
    },
    # ---- Policies (storage / fabric) -----------------------------------------
    'intersight_multicast_policy': {
        'source_ip_proxy_state': 'src_ip_proxy',
    },
    'intersight_storage_policy': {
        'default_drive_state': 'default_drive_mode',
        'secure_jbod_disk_slots': 'secure_jbods',
        'm2_raid_configuration': 'm2_virtual_drive_config',
        'drive_groups': None,
        'global_hot_spares': None,
        'single_drive_raid0_configuration': None,
        'hybrid_slot_configuration:direct_attached_nvme_slots': None,
        'hybrid_slot_configuration:raid_attached_nvme_slots': None,
    },
    'intersight_port_policy': {
        'names': None,
        'pin_groups': 'pin_groups',
        'port_channel_appliances': 'appliance_port_channels',
        'port_channel_ethernet_uplinks': 'ethernet_uplink_port_channels',
        'port_channel_fc_uplinks': 'fc_uplink_port_channels',
        'port_channel_fcoe_uplinks': 'fcoe_uplink_port_channels',
        'port_modes': None,
        'port_role_appliances': 'appliance_ports',
        'port_role_ethernet_uplinks': 'ethernet_uplink_ports',
        'port_role_fc_storage': 'fc_storage_ports',
        'port_role_fc_uplinks': 'fc_uplink_ports',
        'port_role_fcoe_uplinks': 'fcoe_uplink_ports',
        'port_role_servers': 'server_ports',
    },
    'intersight_vlan_policy': {
        'target_platform': None,
    },
    # ---- Policies (fibre channel) -------------------------------------------
    'intersight_fibre_channel_adapter_policy': {
        'adapter_template': None,
        'maximum_luns_per_target': 'lun_count',
    },
    'intersight_fibre_channel_network_policy': {},
    'intersight_fibre_channel_qos_policy': {
        'class_of_service': 'cos',
    },
    'intersight_fibre_channel_zone_policy': {
        'targets': 'fc_target_members',
    },
    # ---- Profiles / Templates ------------------------------------------------
    'intersight_server_profile_template': {
        'adapter_configuration_policy': 'adapter_policy',
        'certificate_management_policy': 'certificate_policy',
    },
    'intersight_server_profile': {
        'adapter_configuration_policy': 'adapter_policy',
        'certificate_management_policy': 'certificate_policy',
    },
}

# Keys that are valid in every module – never dropped by pruning
_UNIVERSAL_KEYS = frozenset({'name', 'description', 'tags', 'organization', 'state',
                              'api_key_id', 'api_private_key', 'api_uri',
                              'validate_certs', 'use_proxy'})

# Valid module param sets for modules that need explicit pruning.
# (Only modules where merge_schema_defaults injects keys the module explicitly
# rejects.  Other modules can tolerate extra keys being silently ignored.)
_MODULE_VALID_PARAMS = {
    'intersight_bios_policy': frozenset({
        'acs_control_gpu1state', 'acs_control_gpu2state', 'acs_control_gpu3state',
        'acs_control_gpu4state', 'acs_control_gpu5state', 'acs_control_gpu6state',
        'acs_control_gpu7state', 'acs_control_gpu8state', 'acs_control_slot11state',
        'acs_control_slot12state', 'acs_control_slot13state', 'acs_control_slot14state',
        'adaptive_refresh_mgmt_level', 'adjacent_cache_line_prefetch', 'advanced_mem_test',
        'all_usb_devices', 'altitude', 'aspm_support', 'assert_nmi_on_perr',
        'assert_nmi_on_serr', 'auto_cc_state', 'autonumous_cstate_enable', 'baud_rate',
        'bme_dma_mitigation', 'boot_option_num_retry', 'boot_option_re_cool_down',
        'boot_option_retry', 'boot_performance_mode', 'burst_and_postponed_refresh',
        'c1auto_demotion', 'c1auto_un_demotion', 'cbs_cmn_apbdis', 'cbs_cmn_cpu_cpb',
        'cbs_cmn_cpu_gen_downcore_ctrl', 'cbs_cmn_cpu_global_cstate_ctrl',
        'cbs_cmn_cpu_l1stream_hw_prefetcher', 'cbs_cmn_cpu_l2stream_hw_prefetcher',
        'cbs_cmn_cpu_smee', 'cbs_cmn_cpu_streaming_stores_ctrl',
        'cbs_cmn_determinism_slider', 'cbs_cmn_efficiency_mode_en',
        'cbs_cmn_fixed_soc_pstate', 'cbs_cmn_gnb_nb_iommu', 'cbs_cmn_gnb_smu_df_cstates',
        'cbs_cmn_gnb_smucppc', 'cbs_cmn_mem_ctrl_bank_group_swap_ddr4',
        'cbs_cmn_mem_map_bank_interleave_ddr4', 'cbs_cmnc_tdp_ctl', 'cbs_cpu_ccd_ctrl_ssp',
        'cbs_cpu_core_ctrl', 'cbs_cpu_smt_ctrl', 'cbs_dbg_cpu_snp_mem_cover',
        'cbs_dbg_cpu_snp_mem_size_cover', 'cbs_df_cmn_acpi_srat_l3numa',
        'cbs_df_cmn_dram_nps', 'cbs_df_cmn_mem_intlv', 'cbs_df_cmn_mem_intlv_size',
        'cbs_sev_snp_support', 'cdn_enable', 'cdn_support', 'channel_inter_leave',
        'cisco_adaptive_mem_training', 'cisco_debug_level', 'cisco_oprom_launch_optimization',
        'cisco_xgmi_max_speed', 'cke_low_policy', 'closed_loop_therm_throtl', 'cmci_enable',
        'config_tdp', 'config_tdp_level', 'console_redirection', 'core_multi_processing',
        'cpu_energy_performance', 'cpu_frequency_floor', 'cpu_pa_limit',
        'cpu_perf_enhancement', 'cpu_performance', 'cpu_power_management', 'cr_qos',
        'crfastgo_config', 'dcpmm_firmware_downgrade', 'demand_scrub', 'direct_cache_access',
        'dma_ctrl_opt_in', 'dram_clock_throttling', 'dram_refresh_rate',
        'dram_sw_thermal_throttling', 'eadr_support', 'edpc_en', 'enable_clock_spread_spec',
        'enable_mktme', 'enable_rmt', 'enable_sgx', 'enable_tme', 'energy_efficient_turbo',
        'eng_perf_tuning', 'enhanced_intel_speed_step_tech', 'epoch_update', 'epp_enable',
        'epp_profile', 'error_check_scrub', 'execute_disable_bit', 'extended_apic',
        'flow_control', 'frb2enable', 'hardware_prefetch', 'hwpm_enable', 'imc_interleave',
        'intel_dynamic_speed_select', 'intel_hyper_threading_tech', 'intel_speed_select',
        'intel_turbo_boost_tech', 'intel_virtualization_technology', 'intel_vt_for_directed_io',
        'intel_vtd_coherency_support', 'intel_vtd_interrupt_remapping',
        'intel_vtd_pass_through_dma_support', 'intel_vtdats_support', 'ioh_error_enable',
        'ioh_resource', 'ip_prefetch', 'ipv4http', 'ipv4pxe', 'ipv6http', 'ipv6pxe',
        'kti_prefetch', 'legacy_os_redirection', 'legacy_usb_support', 'llc_alloc',
        'llc_prefetch', 'lom_port0state', 'lom_port1state', 'lom_port2state', 'lom_port3state',
        'lom_ports_all_state', 'lv_ddr_mode', 'make_device_non_bootable',
        'memory_bandwidth_boost', 'memory_inter_leave', 'memory_mapped_io_above4gb',
        'memory_refresh_rate', 'memory_size_limit', 'memory_thermal_throttling',
        'mirroring_mode', 'mmcfg_base', 'network_stack', 'numa_optimized',
        'nvmdimm_perform_config', 'onboard10gbit_lom', 'onboard_gbit_lom',
        'onboard_scu_storage_support', 'onboard_scu_storage_sw_stack', 'operation_mode',
        'os_boot_watchdog_timer', 'os_boot_watchdog_timer_policy',
        'os_boot_watchdog_timer_timeout', 'out_of_band_mgmt_port', 'package_cstate_limit',
        'panic_high_watermark', 'partial_cache_line_sparing', 'partial_mirror_mode_config',
        'partial_mirror_percent', 'partial_mirror_value1', 'partial_mirror_value2',
        'partial_mirror_value3', 'partial_mirror_value4', 'patrol_scrub',
        'patrol_scrub_duration', 'pc_ie_ras_support', 'pc_ie_ssd_hot_plug_support',
        'pch_pcie_pll_ssc', 'pch_usb30mode', 'pci_option_ro_ms', 'pci_rom_clp',
        'pcie_ari_support', 'pcie_pll_ssc', 'pcie_slot_mraid1link_speed',
        'pcie_slot_mraid1option_rom', 'pcie_slot_mraid2link_speed', 'pcie_slot_mraid2option_rom',
        'pcie_slot_mstorraid_link_speed', 'pcie_slot_mstorraid_option_rom',
        'pcie_slot_nvme1link_speed', 'pcie_slot_nvme1option_rom', 'pcie_slot_nvme2link_speed',
        'pcie_slot_nvme2option_rom', 'pcie_slot_nvme3link_speed', 'pcie_slot_nvme3option_rom',
        'pcie_slot_nvme4link_speed', 'pcie_slot_nvme4option_rom', 'pcie_slot_nvme5link_speed',
        'pcie_slot_nvme5option_rom', 'pcie_slot_nvme6link_speed', 'pcie_slot_nvme6option_rom',
        'pcie_slots_cdn_enable', 'pop_support', 'post_error_pause', 'post_package_repair',
        'processor_c1e', 'processor_c3report', 'processor_c6report', 'processor_cstate',
        'psata', 'pstate_coord_type', 'putty_key_pad', 'pwr_perf_tuning', 'qpi_link_frequency',
        'qpi_link_speed', 'qpi_snoop_mode', 'rank_inter_leave', 'redirection_after_post',
        'sata_mode_select', 'select_memory_ras_configuration', 'select_ppr_type',
        'serial_port_aenable', 'sev', 'sgx_auto_registration_agent', 'sgx_epoch0', 'sgx_epoch1',
        'sgx_factory_reset', 'sgx_le_pub_key_hash0', 'sgx_le_pub_key_hash1',
        'sgx_le_pub_key_hash2', 'sgx_le_pub_key_hash3', 'sgx_le_wr',
        'sgx_package_info_in_band_access', 'sgx_qos', 'sha1pcr_bank', 'sha256pcr_bank',
        'single_pctl_enable', 'slot10link_speed', 'slot10state', 'slot11link_speed',
        'slot11state', 'slot12link_speed', 'slot12state', 'slot13state', 'slot14state',
        'slot1link_speed', 'slot1state', 'slot2link_speed', 'slot2state', 'slot3link_speed',
        'slot3state', 'slot4link_speed', 'slot4state', 'slot5link_speed', 'slot5state',
        'slot6link_speed', 'slot6state', 'slot7link_speed', 'slot7state', 'slot8link_speed',
        'slot8state', 'slot9link_speed', 'slot9state', 'slot_flom_link_speed',
        'slot_front_nvme1link_speed', 'slot_front_nvme1option_rom', 'slot_front_nvme2link_speed',
        'slot_front_nvme2option_rom', 'slot_front_nvme3link_speed', 'slot_front_nvme3option_rom',
        'slot_front_nvme4link_speed', 'slot_front_nvme4option_rom', 'slot_front_nvme5link_speed',
        'slot_front_nvme5option_rom', 'slot_front_nvme6link_speed', 'slot_front_nvme6option_rom',
        'slot_front_nvme7link_speed', 'slot_front_nvme7option_rom', 'slot_front_nvme8link_speed',
        'slot_front_nvme8option_rom', 'slot_front_nvme9link_speed', 'slot_front_nvme9option_rom',
        'slot_front_nvme10link_speed', 'slot_front_nvme10option_rom',
        'slot_front_nvme11link_speed', 'slot_front_nvme11option_rom',
        'slot_front_nvme12link_speed', 'slot_front_nvme12option_rom',
        'slot_front_slot5link_speed', 'slot_front_slot6link_speed',
        'slot_gpu1state', 'slot_gpu2state', 'slot_gpu3state', 'slot_gpu4state',
        'slot_gpu5state', 'slot_gpu6state', 'slot_gpu7state', 'slot_gpu8state',
        'slot_hba_link_speed', 'slot_hba_state', 'slot_lom1link', 'slot_lom2link',
        'slot_mezz_state', 'slot_mlom_link_speed', 'slot_mlom_state', 'slot_mraid_link_speed',
        'slot_mraid_state', 'slot_n1state', 'slot_n2state', 'slot_n3state', 'slot_n4state',
        'slot_n5state', 'slot_n6state', 'slot_n7state', 'slot_n8state', 'slot_n9state',
        'slot_n10state', 'slot_n11state', 'slot_n12state', 'slot_n13state', 'slot_n14state',
        'slot_n15state', 'slot_n16state', 'slot_n17state', 'slot_n18state', 'slot_n19state',
        'slot_n20state', 'slot_n21state', 'slot_n22state', 'slot_n23state', 'slot_n24state',
        'slot_raid_link_speed', 'slot_raid_state', 'slot_rear_nvme1link_speed',
        'slot_rear_nvme1state', 'slot_rear_nvme2link_speed', 'slot_rear_nvme2state',
        'slot_rear_nvme3link_speed', 'slot_rear_nvme3state', 'slot_rear_nvme4link_speed',
        'slot_rear_nvme4state', 'slot_rear_nvme5state', 'slot_rear_nvme6state',
        'slot_rear_nvme7state', 'slot_rear_nvme8state', 'slot_riser1link_speed',
        'slot_riser1slot1link_speed', 'slot_riser1slot2link_speed', 'slot_riser1slot3link_speed',
        'slot_riser2link_speed', 'slot_riser2slot4link_speed', 'slot_riser2slot5link_speed',
        'slot_riser2slot6link_speed', 'slot_sas_state', 'slot_ssd_slot1link_speed',
        'slot_ssd_slot2link_speed', 'smee', 'smt_mode', 'snc', 'snoopy_mode_for2lm',
        'snoopy_mode_for_ad', 'sparing_mode', 'sr_iov', 'streamer_prefetch', 'svm_mode',
        'terminal_type', 'tpm_control', 'tpm_pending_operation', 'tpm_ppi_required',
        'tpm_support', 'tsme', 'txt_support', 'ucsm_boot_order_rule', 'ufs_disable',
        'uma_based_clustering', 'upi_link_enablement', 'upi_power_management', 'usb_emul6064',
        'usb_port_front', 'usb_port_internal', 'usb_port_kvm', 'usb_port_rear',
        'usb_port_sd_card', 'usb_port_vmedia', 'usb_xhci_support', 'vga_priority',
        'virtual_numa', 'vmd_enable', 'vol_memory_mode', 'work_load_config', 'x2apic_opt_out',
        'xpt_prefetch', 'xpt_remote_prefetch',
    }),
}


# ---------------------------------------------------------------------------
# Helper: schema default extraction
# ---------------------------------------------------------------------------

def _resolve_ref(ref, definitions):
    """Resolve a JSON Schema $ref string to the referenced definition dict."""
    key = ref.lstrip('#/').removeprefix('definitions/')
    return definitions.get(key, {})


def _extract_defaults(node, definitions, _depth=0):
    """
    Recursively walk *node* and return a flat dict of
    {property_name: default_value} for all properties carrying 'default'.
    Resolves $ref and allOf transparently.
    """
    if _depth > 12:
        return {}
    defaults = {}
    if '$ref' in node:
        defaults.update(_extract_defaults(
            _resolve_ref(node['$ref'], definitions), definitions, _depth + 1))
    for sub in node.get('allOf', []):
        defaults.update(_extract_defaults(sub, definitions, _depth + 1))
    for prop_name, prop_schema in node.get('properties', {}).items():
        if 'default' in prop_schema:
            defaults[prop_name] = prop_schema['default']
        elif '$ref' in prop_schema:
            resolved = _resolve_ref(prop_schema['$ref'], definitions)
            if 'default' in resolved:
                defaults[prop_name] = resolved['default']
    return defaults


# ---------------------------------------------------------------------------
# Block size calculation helpers
# ---------------------------------------------------------------------------

def _wwn_hex_to_int(wwn_str):
    """Convert WWN hex string (e.g. '20:00:00:25:B5:00:00:00') to integer."""
    if not isinstance(wwn_str, str):
        return None
    try:
        return int(wwn_str.replace(':', ''), 16)
    except (ValueError, AttributeError):
        return None


def _int_to_wwn_hex(value):
    """Convert integer to WWN hex string (e.g. '20:00:00:25:B5:00:00:00')."""
    if not isinstance(value, int):
        return None
    try:
        hex_str = format(value, '016x')
        return ':'.join(hex_str[i:i+2] for i in range(0, 16, 2))
    except (ValueError, AttributeError):
        return None


def _calculate_size_from_range(block, from_key):
    """Calculate size from from/to in a block, given the from_key name.
    Returns updated block dict or None if no update needed.
    """
    if not isinstance(block, dict):
        return None
    if 'to' not in block or 'size' in block:
        return None  # to not present or size already exists
    from_val = block.get(from_key)
    to_val = block.get('to')
    if from_val is None or to_val is None:
        return None
    # For integer-based ranges (IQN)
    if isinstance(from_val, int) and isinstance(to_val, int):
        return {'size': to_val - from_val + 1}
    # For hex string ranges (WWN)
    if isinstance(from_val, str) and isinstance(to_val, str):
        from_int = _wwn_hex_to_int(from_val)
        to_int = _wwn_hex_to_int(to_val)
        if from_int is not None and to_int is not None:
            return {'size': to_int - from_int + 1}

        # For IP-address ranges (IPv4 / IPv6)
        try:
            from_ip = ipaddress.ip_address(from_val)
            to_ip = ipaddress.ip_address(to_val)
            if from_ip.version == to_ip.version:
                return {'size': int(to_ip) - int(from_ip) + 1}
        except ValueError:
            pass
    return None


def _process_blocks_with_size(blocks, from_key, drop_to=False):
    """Process blocks list and calculate size from to/from if needed.
    from_key is the name of the 'from' field in the block dict (e.g. 'from', 'iqn_from', 'wwn_from').
    """
    if not isinstance(blocks, list):
        return blocks
    converted = []
    for block in blocks:
        if isinstance(block, dict):
            new_block = dict(block)
            size_calc = _calculate_size_from_range(new_block, from_key)
            if size_calc:
                new_block.update(size_calc)
            if drop_to:
                new_block.pop('to', None)
            converted.append(new_block)
        else:
            converted.append(block)
    return converted


def _select_port_policy_side(value, index):
    """
    Split helper for port policy attributes.
    If value is a list-of-lists, select index 0 or 1 (fallback to 0).
    Otherwise, keep the original value for both split policies.
    """
    if not isinstance(value, list):
        return value
    if not value:
        return value
    if any(isinstance(v, list) for v in value):
        selected = value[index] if index < len(value) else value[0]
        if isinstance(selected, list):
            return selected
        return [selected]
    return value


def _select_index_or_first(values, index):
    """Return values[index] when available, else values[0]."""
    if not isinstance(values, list) or len(values) == 0:
        return values
    if index < len(values):
        return values[index]
    return values[0]


def _split_port_policy_entries_by_name(entries, index):
    """
    Split per-policy values inside each port policy entry.

    Rules:
      - pc_ids: choose by policy index, fallback to first value.
      - vsan_ids: choose by policy index, fallback to first value.
    """
    if not isinstance(entries, list):
        return entries

    split_entries = []
    for entry in entries:
        if not isinstance(entry, dict):
            split_entries.append(entry)
            continue

        new_entry = dict(entry)

        pc_ids = entry.get('pc_ids')
        if isinstance(pc_ids, list) and len(pc_ids) > 0:
            new_entry['pc_ids'] = [_select_index_or_first(pc_ids, index)]

        vsan_ids = entry.get('vsan_ids')
        if isinstance(vsan_ids, list) and len(vsan_ids) > 0:
            new_entry['vsan_ids'] = [_select_index_or_first(vsan_ids, index)]

        split_entries.append(new_entry)

    return split_entries


def _expand_lcp_vnics(vnics, policy_placement_mode=None):
    """Expand schema vnics entries into module vnics entries.

    Each vNIC entry can define one or two `names`. For each name, emit one
    module vNIC payload. For list-valued fields, choose by index with fallback
    to the first value when the list has only one item.
    """
    if not isinstance(vnics, list):
        return vnics

    expanded = []
    for vnic in vnics:
        if not isinstance(vnic, dict):
            continue

        names = vnic.get('names', [])
        if not isinstance(names, list) or len(names) == 0:
            continue

        # Keep behavior consistent with policy splitting: one or two only.
        for idx, vnic_name in enumerate(names[:2]):
            out = {'name': vnic_name}

            # Derive module auto-placement flag from policy-level placement mode.
            if isinstance(policy_placement_mode, str):
                out['auto_vnic_placement_enabled'] = (policy_placement_mode.lower() == 'auto')

            # Basic per-vNIC mappings
            key_map = {
                'cdn_source': 'cdn_source',
                'enable_failover': 'failover_enabled',
                'ethernet_adapter_policy': 'eth_adapter_policy_name',
                'ethernet_network_control_policy': 'fabric_eth_network_control_policy_name',
                'ethernet_network_policy': 'eth_network_policy_name',
                'ethernet_qos_policy': 'eth_qos_policy_name',
            }
            for src, dst in key_map.items():
                if src in vnic:
                    out[dst] = vnic[src]

            # Per-name list fields on vNIC object
            list_map = {
                'cdn_values': 'cdn_value',
                'ethernet_network_group_policies': 'fabric_eth_network_group_policy_name',
                'iscsi_boot_policies': 'iscsi_boot_policy_name',
                'mac_address_pools': 'mac_pool_name',
                'mac_addresses_static': 'static_mac_address',
                'pin_group_names': 'pin_group_name',
            }
            for src, dst in list_map.items():
                values = vnic.get(src)
                if isinstance(values, list) and len(values) > 0:
                    out[dst] = _select_index_or_first(values, idx)

            # Placement sub-structure
            placement = vnic.get('placement', {})
            if isinstance(placement, dict):
                placement_map = {
                    'automatic_slot_id_assignment': 'auto_slot_id',
                    'automatic_pci_link_assignment': 'auto_pci_link',
                }
                for src, dst in placement_map.items():
                    if src in placement:
                        out[dst] = placement[src]

                placement_list_map = {
                    'pci_order': 'order',
                    'slot_ids': 'placement_slot_id',
                    'switch_ids': 'switch_id',
                    'uplink_ports': 'uplink_port',
                    'pci_links': 'pci_link',
                }
                for src, dst in placement_list_map.items():
                    values = placement.get(src)
                    if isinstance(values, list) and len(values) > 0:
                        out[dst] = _select_index_or_first(values, idx)

                # Derive pci_link_assignment_mode because schema models this as
                # automatic/manual placement knobs plus optional pci_links.
                auto_pci = placement.get('automatic_pci_link_assignment')
                if isinstance(auto_pci, bool):
                    if auto_pci is False:
                        pci_links = placement.get('pci_links')
                        if isinstance(pci_links, list) and len(pci_links) > 0:
                            out['pci_link_assignment_mode'] = 'Custom'
                        else:
                            out['pci_link_assignment_mode'] = 'Load-Balanced'

            # Connection-type specific settings
            sriov = vnic.get('sriov', {})
            if isinstance(sriov, dict) and sriov:
                sriov_settings = {}
                sriov_map = {
                    'enabled': 'enabled',
                    'number_of_vfs': 'vf_count',
                    'receive_queue_count_per_vf': 'rx_count_per_vf',
                    'transmit_queue_count_per_vf': 'tx_count_per_vf',
                    'completion_queue_count_per_vf': 'comp_count_per_vf',
                    'interrupt_count_per_vf': 'int_count_per_vf',
                }
                for src, dst in sriov_map.items():
                    if src in sriov:
                        sriov_settings[dst] = sriov[src]
                if sriov_settings:
                    out['connection_type'] = 'sriov'
                    out['sriov_settings'] = sriov_settings

            usnic = vnic.get('usnic', {})
            if isinstance(usnic, dict) and usnic and 'connection_type' not in out:
                usnic_settings = {}
                usnic_map = {
                    'number_of_usnics': 'count',
                    'class_of_service': 'cos',
                    'usnic_adapter_policy': 'usnic_adapter_policy_name',
                }
                for src, dst in usnic_map.items():
                    if src in usnic:
                        usnic_settings[dst] = usnic[src]
                if usnic_settings:
                    out['connection_type'] = 'usnic'
                    out['usnic_settings'] = usnic_settings

            vmq = vnic.get('vmq', {})
            if isinstance(vmq, dict) and vmq and 'connection_type' not in out:
                vmq_settings = {}
                vmq_map = {
                    'enabled': 'enabled',
                    'enable_virtual_machine_multi_queue': 'multi_queue_support',
                    'number_of_interrupts': 'num_interrupts',
                    'number_of_virtual_machine_queues': 'num_vmqs',
                    'number_of_sub_vnics': 'num_sub_vnics',
                    'vmmq_adapter_policy': 'vmmq_adapter_policy_name',
                }
                for src, dst in vmq_map.items():
                    if src in vmq:
                        vmq_settings[dst] = vmq[src]
                if vmq_settings:
                    out['connection_type'] = 'vmq'
                    out['vmq_settings'] = vmq_settings

            # Schema-aligned defaults for commonly requested module fields.
            # merge_schema_defaults only applies at policy root, not nested vNIC
            # entries, so we set nested defaults here.
            out.setdefault('cdn_source', 'vnic')
            out.setdefault('auto_slot_id', True)
            out.setdefault('auto_pci_link', True)
            out.setdefault('failover_enabled', False)
            if out.get('auto_pci_link') is False:
                out.setdefault('pci_link', 0)

            # If PCI auto-assignment is disabled and no explicit mode was
            # inferred above, default to Load-Balanced.
            if out.get('auto_pci_link') is False:
                out.setdefault('pci_link_assignment_mode', 'Load-Balanced')

            # When auto assignment is enabled, explicit values must not be set.
            if out.get('auto_pci_link') is True:
                out.pop('pci_link', None)
                out.pop('pci_link_assignment_mode', None)
            if out.get('auto_slot_id') is True:
                out.pop('placement_slot_id', None)

            expanded.append(out)

    return expanded


def _validate_and_read_pem_file(file_path):
    """Validate and read PEM-formatted file content from disk."""
    if not isinstance(file_path, str) or not file_path.strip():
        raise ValueError("File path must be a non-empty string")

    resolved_path = os.path.expandvars(os.path.expanduser(file_path.strip()))

    if not os.path.exists(resolved_path):
        raise ValueError(f"Certificate file does not exist: {file_path}")
    if not os.path.isfile(resolved_path):
        raise ValueError(f"Path is not a file: {file_path}")
    if not os.access(resolved_path, os.R_OK):
        raise ValueError(f"Certificate file is not readable: {file_path}")

    try:
        with open(resolved_path, 'r') as file_handle:
            content = file_handle.read()
    except Exception as exc:
        raise ValueError(f"Failed to read certificate file {file_path}: {exc}")

    # Ensure the input has PEM begin/end blocks with matching labels.
    block_pattern = re.compile(
        r'-----BEGIN ([A-Z0-9 ]+)-----\s+([A-Za-z0-9+/=\r\n]+)\s+-----END \1-----',
        re.MULTILINE,
    )
    if not block_pattern.search(content):
        raise ValueError(f"File is not a valid PEM formatted file: {file_path}")

    return content


def _expand_scp_vhbas(vhbas):
    """Expand schema vhbas entries into module vhbas entries.

    Each vHBA entry can define one or two `names`. For each name, emit one
    module vHBA payload. For split-list fields, choose by index with fallback
    to first value when list has one item.
    """
    if not isinstance(vhbas, list):
        return vhbas

    expanded = []
    for vhba in vhbas:
        if not isinstance(vhba, dict):
            continue

        names = vhba.get('names', [])
        if not isinstance(names, list) or len(names) == 0:
            continue

        for idx, vhba_name in enumerate(names[:2]):
            out = {'name': vhba_name}

            key_map = {
                'vhba_type': 'vhba_type',
                'persistent_lun_bindings': 'persistent_lun_bindings',
                'fibre_channel_adapter_policy': 'fibre_channel_adapter_policy',
                'fibre_channel_qos_policy': 'fibre_channel_qos_policy',
            }
            for src, dst in key_map.items():
                if src in vhba:
                    out[dst] = vhba[src]

            split_scalar_list_map = {
                'fibre_channel_network_policies': 'fibre_channel_network_policy',
                'pin_group_names': 'pin_group_name',
                'wwpn_pools': 'wwpn_pool',
                'wwpn_static_addresses': 'static_wwpn_address',
            }
            for src, dst in split_scalar_list_map.items():
                values = vhba.get(src)
                if isinstance(values, list) and len(values) > 0:
                    out[dst] = _select_index_or_first(values, idx)

            # Optional zone policies are list-valued at module input as well.
            fc_zone_policies = vhba.get('fc_zone_policies')
            if isinstance(fc_zone_policies, list) and len(fc_zone_policies) > 0:
                if any(isinstance(v, list) for v in fc_zone_policies):
                    selected = _select_index_or_first(fc_zone_policies, idx)
                    if isinstance(selected, list):
                        out['fibre_channel_zone_policies'] = selected
                    else:
                        out['fibre_channel_zone_policies'] = [selected]
                else:
                    out['fibre_channel_zone_policies'] = fc_zone_policies

            placement = vhba.get('placement', {})
            if isinstance(placement, dict):
                if 'automatic_slot_id_assignment' in placement:
                    out['auto_slot_id'] = placement['automatic_slot_id_assignment']
                if 'automatic_pci_link_assignment' in placement:
                    out['auto_pci_link'] = placement['automatic_pci_link_assignment']

                placement_list_map = {
                    'pci_order': 'pci_order',
                    'slot_ids': 'slot_id',
                    'uplink_ports': 'uplink_port',
                    'pci_links': 'pci_link',
                    'switch_ids': 'switch_id',
                }
                for src, dst in placement_list_map.items():
                    values = placement.get(src)
                    if isinstance(values, list) and len(values) > 0:
                        selected = _select_index_or_first(values, idx)
                        if dst == 'switch_id' and isinstance(selected, str):
                            out[dst] = selected.lower()
                        else:
                            out[dst] = selected

                auto_pci = placement.get('automatic_pci_link_assignment')
                if isinstance(auto_pci, bool) and auto_pci is False:
                    pci_links = placement.get('pci_links')
                    if isinstance(pci_links, list) and len(pci_links) > 0:
                        out['pci_link_assignment_mode'] = 'custom'
                    else:
                        out['pci_link_assignment_mode'] = 'load-balanced'

            # Nested schema defaults (not applied by root merge)
            out.setdefault('vhba_type', 'fc-initiator')
            out.setdefault('persistent_lun_bindings', False)
            out.setdefault('auto_slot_id', True)
            out.setdefault('auto_pci_link', True)
            out.setdefault('pci_link', 0)
            out.setdefault('uplink_port', 0)
            out.setdefault('pci_order', 0)
            out.setdefault('switch_id', 'a')
            out.setdefault('wwpn_address_type', 'pool')

            if out.get('auto_pci_link') is False:
                out.setdefault('pci_link_assignment_mode', 'load-balanced')
            if out.get('auto_pci_link') is True:
                out.pop('pci_link', None)
                out.pop('pci_link_assignment_mode', None)
            if out.get('auto_slot_id') is True:
                out.pop('slot_id', None)

            expanded.append(out)

    return expanded


def split_port_policies(item, name_prefix='', name_suffix=''):
    """
    Expand schema `intersight.port` object into one or two policy payloads.

    `names` drives split behavior:
      - first policy uses names[0]
      - second policy uses names[1] if present, else names[0]

    For split-capable list-of-lists fields, policy #1 gets index 0 and
    policy #2 gets index 1 (fallback to index 0).
    """
    if not isinstance(item, dict):
        return [item]

    names = item.get('names')
    if not isinstance(names, list) or len(names) == 0:
        # Backward-compatible fallback when names isn't supplied.
        single = dict(item)
        if 'name' in single and isinstance(single.get('name'), str):
            single['name'] = f"{name_prefix}{single['name']}{name_suffix}"
        return [single]

    split_keys = {
        'pin_groups',
        'port_channel_appliances',
        'port_channel_ethernet_uplinks',
        'port_channel_fc_uplinks',
        'port_channel_fcoe_uplinks',
        'port_modes',
        'port_role_appliances',
        'port_role_ethernet_uplinks',
        'port_role_fc_storage',
        'port_role_fc_uplinks',
        'port_role_fcoe_uplinks',
        'port_role_servers',
    }

    per_entry_id_split_keys = {
        'port_channel_appliances',
        'port_channel_ethernet_uplinks',
        'port_channel_fc_uplinks',
        'port_channel_fcoe_uplinks',
        'port_role_fc_storage',
        'port_role_fc_uplinks',
    }

    # Emit one payload for one name and two for two names.
    # If more than two names are provided, only the first two are used.
    policy_names = names[:2]
    expanded = []

    for idx, policy_name in enumerate(policy_names):
        split_item = {}
        for key, value in item.items():
            if key == 'names':
                continue
            if key in split_keys:
                split_value = _select_port_policy_side(value, idx)
                if key in per_entry_id_split_keys:
                    split_value = _split_port_policy_entries_by_name(split_value, idx)
                split_item[key] = split_value
            else:
                split_item[key] = value
        split_item['name'] = f"{name_prefix}{policy_name}{name_suffix}"
        expanded.append(split_item)

    return expanded


# ---------------------------------------------------------------------------
# Public filter functions
# ---------------------------------------------------------------------------

def merge_schema_defaults(item, schema, definition_key):
    """
    Return schema defaults for *definition_key* merged with *item*.
    User-provided values always win.
    """
    definitions = schema.get('definitions', {})
    if definition_key not in definitions:
        return item
    defaults = _extract_defaults(definitions[definition_key], definitions)

    # Allow policy templates to pre-populate values before applying user input.
    # Explicit values in the policy item always override template values.
    template_sources = {
        'intersight.bios': ('bios_template', 'intersight.bios.templates'),
        'intersight.ethernet_adapter': ('adapter_template', 'intersight.ethernet_adapter.templates'),
        'intersight.fibre_channel_adapter': ('adapter_template', 'intersight.fibre_channel_adapter.templates'),
    }
    if isinstance(item, dict) and definition_key in template_sources:
        template_key_field, template_def_key = template_sources[definition_key]
        template_name = item.get(template_key_field)
        templates = definitions.get(template_def_key, {})
        template_map = templates.get('properties', {}) if isinstance(templates, dict) else {}
        if isinstance(template_name, str) and isinstance(template_map, dict):
            template_values = template_map.get(template_name)
            if isinstance(template_values, dict):
                defaults.update(template_values)

    merged = {}
    merged.update(defaults)
    merged.update(item)

    # For System QoS policies, optionally replace classes with schema templates
    # and enforce MTU on every class based on jumbo_mtu.
    if definition_key == 'intersight.system_qos' and isinstance(merged, dict):
        templates_def = definitions.get('intersight.system_qos.templates', {})
        template_props = templates_def.get('properties', {}) if isinstance(templates_def, dict) else {}

        use_recommended = bool(merged.get('configure_recommended_classes'))
        use_default = bool(merged.get('configure_default_classes'))

        template_key = None
        if use_recommended:
            template_key = 'configure_recommended_classes'
        elif use_default:
            template_key = 'configure_default_classes'

        if template_key and isinstance(template_props, dict):
            template_entry = template_props.get(template_key)
            if isinstance(template_entry, dict):
                template_classes = template_entry.get('classes')
                if isinstance(template_classes, list):
                    merged['classes'] = copy.deepcopy(template_classes)

        classes = merged.get('classes')
        if isinstance(classes, list):
            mtu_value = 9216 if bool(merged.get('jumbo_mtu', True)) else 1500
            updated = []
            for class_entry in classes:
                if isinstance(class_entry, dict):
                    new_entry = dict(class_entry)
                    class_name = new_entry.get('name')
                    if isinstance(class_name, str) and class_name.strip().lower() == 'fc':
                        new_entry['mtu'] = 2240
                    else:
                        new_entry['mtu'] = mtu_value
                    updated.append(new_entry)
                else:
                    updated.append(class_entry)
            merged['classes'] = updated

    return merged


def to_module_params(item, module_name):
    """
    Translate schema model keys to cisco.intersight module parameter names.

    Steps performed (in order):
      1. Apply per-module key renames (schema key → module param name).
         Keys mapped to None are dropped.
      2. Expand well-known complex nested structures into flat module params.
      3. Prune keys not accepted by modules that have a strict valid-param set
         (e.g. intersight_bios_policy injects AMD-specific schema defaults that
         the module's argument_spec does not recognise).

    Keys not listed in the rename table are passed through unchanged.
    """
    renames = _MODULE_KEY_RENAMES.get(module_name, {})
    result = {}

    for key, value in item.items():
        if key in renames:
            new_key = renames[key]
            if new_key is None:
                continue           # explicitly dropped
            result[new_key] = value
        else:
            result[key] = value

    # ---- Module-specific complex expansions ----------------------------------

    if   module_name == 'intersight_adapter_config_policy':
        settings = result.get('settings')
        if isinstance(settings, list):
            converted = []
            for setting in settings:
                if not isinstance(setting, dict):
                    continue
                new_setting = dict(setting)
                if 'pci_slot' in new_setting:
                    new_setting['slot_id'] = new_setting.pop('pci_slot')
                # Module expects flattened FEC keys inside each settings entry.
                dce_settings = new_setting.pop('dce_interface_settings', None)
                if isinstance(dce_settings, dict):
                    for fec_key in (
                        'dce_interface_1_fec_mode',
                        'dce_interface_2_fec_mode',
                        'dce_interface_3_fec_mode',
                        'dce_interface_4_fec_mode',
                    ):
                        if fec_key in dce_settings:
                            new_setting[fec_key] = dce_settings[fec_key]
                # The module does not expose this setting; it is hardcoded false.
                new_setting.pop('enable_physical_nic_mode', None)
                converted.append(new_setting)
            result['settings'] = converted

    elif module_name == 'intersight_boot_order_policy':
        boot_devices = result.get('boot_devices')
        if isinstance(boot_devices, list):
            device_type_map = {
                'iscsi': 'iSCSI',
                'local_cdd': 'Local CDD',
                'local_disk': 'Local Disk',
                'nvme': 'NVMe',
                'pch_storage': 'PCH Storage',
                'pxe': 'PXE',
                'san': 'SAN',
                'sd_card': 'SD Card',
                'uefi_shell': 'UEFI Shell',
                'usb': 'USB',
                'virtual_media': 'Virtual Media',
            }
            converted = []
            for boot_device in boot_devices:
                if not isinstance(boot_device, dict):
                    converted.append(boot_device)
                    continue
                new_boot_device = dict(boot_device)
                device_type = new_boot_device.get('device_type')
                normalized_type = None
                if isinstance(device_type, str):
                    normalized_type = device_type.strip().lower().replace('-', '_').replace(' ', '_')
                    if normalized_type in device_type_map:
                        new_boot_device['device_type'] = device_type_map[normalized_type]

                # Schema uses generic field names; module expects device-specific keys.
                if 'slot' in new_boot_device and 'controller_slot' not in new_boot_device:
                    new_boot_device['controller_slot'] = new_boot_device.pop('slot')

                subtype = new_boot_device.pop('subtype', None)
                if subtype not in (None, ''):
                    if normalized_type == 'virtual_media':
                        new_boot_device['virtual_media_subtype'] = subtype
                    elif normalized_type == 'usb':
                        new_boot_device['usb_subtype'] = subtype
                    elif normalized_type == 'sd_card':
                        new_boot_device['sd_card_subtype'] = subtype
                converted.append(new_boot_device)
            result['boot_devices'] = converted

    elif module_name == 'intersight_certificate_management_policy':
        # Handle certificate file reading and PEM validation
        result.pop('assigned_sensitive_data', None)
        certificates = result.get('certificates', [])
        if isinstance(certificates, list):
            processed_certs = []
            for cert_index, cert in enumerate(certificates, start=1):
                if not isinstance(cert, dict):
                    processed_certs.append(cert)
                    continue
                
                new_cert = dict(cert)
                cert_type = new_cert.get('type', 'IMC')
                if isinstance(cert_type, str):
                    cert_type = cert_type.lower()
                new_cert['certificate_type'] = cert_type
                cert_file = new_cert.get('certificate_file')
                key_file = new_cert.get('private_key_file')
                
                # Validate file requirements based on certificate type
                if cert_type == 'imc':
                    # IMC certificates require both certificate_file and private_key_file
                    if not cert_file:
                        raise ValueError(
                            f"IMC certificate '{new_cert.get('name', 'unknown')}' requires 'certificate_file' field"
                        )
                    if not key_file:
                        raise ValueError(
                            f"IMC certificate '{new_cert.get('name', 'unknown')}' requires 'private_key_file' field"
                        )
                    
                    # Read and validate both files
                    try:
                        cert_content = _validate_and_read_pem_file(cert_file)
                        key_content = _validate_and_read_pem_file(key_file)
                        new_cert['certificate'] = cert_content
                        new_cert['private_key'] = key_content
                    except ValueError as e:
                        raise ValueError(
                            f"Error processing IMC certificate '{new_cert.get('name', 'unknown')}': {str(e)}"
                        )
                
                elif cert_type == 'rootca':
                    # RootCA certificates require only certificate_file
                    if not cert_file:
                        raise ValueError(
                            f"RootCA certificate '{new_cert.get('name', 'unknown')}' requires 'certificate_file' field"
                        )
                    
                    # Read and validate certificate file
                    try:
                        cert_content = _validate_and_read_pem_file(cert_file)
                        new_cert['certificate'] = cert_content
                    except ValueError as e:
                        raise ValueError(
                            f"Error processing RootCA certificate '{new_cert.get('name', 'unknown')}': {str(e)}"
                        )
                
                # Remove schema-only fields (won't be sent to API)
                cert_name = new_cert.pop('name', None)
                if cert_name not in (None, ''):
                    new_cert['certificate_name'] = cert_name
                elif cert_type == 'rootca':
                    policy_name = result.get('name', 'certificate')
                    new_cert['certificate_name'] = f"{policy_name}_{cert_index}"

                new_cert.pop('type', None)
                new_cert.pop('certificate_file', None)
                new_cert.pop('private_key_file', None)
                new_cert.pop('variable_id', None)  # deprecated field
                
                processed_certs.append(new_cert)

            result['certificates'] = processed_certs

    elif module_name == 'intersight_drive_security_policy':
        # Resolve sensitive variable identifiers to environment values and map
        # schema structures to module-native manual_key/remote_key dictionaries.
        def _resolve_sensitive_value(var_id, env_prefix):
            if not isinstance(var_id, int) or var_id <= 0:
                return None
            return os.environ.get(f'{env_prefix}_{var_id}')

        manual_key = result.get('manual_key')
        if isinstance(manual_key, dict):
            new_manual = {}

            existing_var_id = manual_key.get('current_security_key_passphrase')
            existing_value = _resolve_sensitive_value(existing_var_id, 'drive_security_current_security_key_passphrase')
            if existing_value not in (None, ''):
                new_manual['existing_key'] = str(existing_value)

            new_var_id = manual_key.get('new_security_key_passphrase')
            new_value = _resolve_sensitive_value(new_var_id, 'drive_security_new_security_key_passphrase')
            if new_value not in (None, ''):
                new_manual['new_key'] = str(new_value)

            result['manual_key'] = new_manual

        remote_key = result.get('remote_key')
        if isinstance(remote_key, dict):
            new_remote = {}

            existing_var_id = remote_key.get('current_security_key_passphrase')
            existing_value = _resolve_sensitive_value(existing_var_id, 'drive_security_current_security_key_passphrase')
            if existing_value not in (None, ''):
                new_remote['existing_key'] = str(existing_value)

            cert_var_id = remote_key.get('server_public_root_ca_certificate')
            cert_value = _resolve_sensitive_value(cert_var_id, 'drive_security_server_ca_certificate')
            if cert_value in (None, ''):
                if isinstance(cert_var_id, int) and cert_var_id > 0:
                    cert_value = os.environ.get(
                        f'drive_security_server_public_root_ca_certificate_{cert_var_id}'
                    )
            if cert_value in (None, ''):
                # Support the unsuffixed variable form used by Terraform inputs.
                fallback_cert_value = (
                    os.environ.get('drive_security_server_ca_certificate')
                    or os.environ.get('drive_security_server_public_root_ca_certificate')
                )
                if fallback_cert_value not in (None, ''):
                    if os.path.isfile(fallback_cert_value):
                        try:
                            cert_value = _validate_and_read_pem_file(fallback_cert_value)
                        except ValueError:
                            cert_value = fallback_cert_value
                    else:
                        cert_value = fallback_cert_value
            if cert_value in (None, ''):
                # Final fallback for bundled sample models in this repository.
                sample_ca = os.path.normpath(
                    os.path.join(os.path.dirname(__file__), '..', '..', 'openshift', 'oath_ldap', 'ca.crt')
                )
                if os.path.isfile(sample_ca):
                    try:
                        cert_value = _validate_and_read_pem_file(sample_ca)
                    except ValueError:
                        cert_value = None
            if cert_value not in (None, ''):
                new_remote['server_certificate'] = str(cert_value)

            auth = remote_key.get('enable_authentication')
            if isinstance(auth, dict):
                new_remote['use_authentication'] = True
                username = auth.get('username')
                if username not in (None, ''):
                    new_remote['username'] = str(username)
                password_var_id = auth.get('password')
                password_value = _resolve_sensitive_value(password_var_id, 'drive_security_authentication_password')
                if password_value not in (None, ''):
                    new_remote['password'] = str(password_value)

            primary = remote_key.get('primary_server')
            if isinstance(primary, dict):
                primary_server = {'enable_drive_security': True}
                if primary.get('hostname_ip_address') not in (None, ''):
                    primary_server['ip_address'] = primary['hostname_ip_address']
                if primary.get('port') not in (None, ''):
                    primary_server['port'] = primary['port']
                if primary.get('timeout') not in (None, ''):
                    primary_server['timeout'] = primary['timeout']
                new_remote['primary_server'] = primary_server

            secondary = remote_key.get('secondary_server')
            if isinstance(secondary, dict):
                secondary_server = {'enable_drive_security': True}
                if secondary.get('hostname_ip_address') not in (None, ''):
                    secondary_server['ip_address'] = secondary['hostname_ip_address']
                if secondary.get('port') not in (None, ''):
                    secondary_server['port'] = secondary['port']
                if secondary.get('timeout') not in (None, ''):
                    secondary_server['timeout'] = secondary['timeout']
                new_remote['secondary_server'] = secondary_server

            if 'server_certificate' in new_remote:
                result['remote_key'] = new_remote
            else:
                result.pop('remote_key', None)

    elif module_name == 'intersight_ethernet_network_group_policy':
        # The module marks allowed_vlans and qinq_vlan as mutually exclusive.
        if result.get('allowed_vlans') not in (None, ''):
            result.pop('qinq_vlan', None)

        def _vlan_is_allowed(native_vlan, allowed_vlans):
            try:
                native = int(native_vlan)
            except (TypeError, ValueError):
                return False

            if isinstance(allowed_vlans, int):
                return native == allowed_vlans
            if isinstance(allowed_vlans, list):
                return any(_vlan_is_allowed(native, entry) for entry in allowed_vlans)
            if not isinstance(allowed_vlans, str):
                return False

            for chunk in allowed_vlans.split(','):
                token = chunk.strip()
                if not token:
                    continue
                if '-' in token:
                    bounds = token.split('-', 1)
                    try:
                        start = int(bounds[0].strip())
                        end = int(bounds[1].strip())
                    except ValueError:
                        continue
                    if start <= native <= end:
                        return True
                else:
                    try:
                        if int(token) == native:
                            return True
                    except ValueError:
                        continue
            return False

        allowed_vlans = result.get('allowed_vlans')
        native_vlan = result.get('native_vlan')
        if native_vlan not in (None, '') and allowed_vlans not in (None, ''):
            if not _vlan_is_allowed(native_vlan, allowed_vlans):
                result.pop('native_vlan', None)

    elif module_name == 'intersight_firmware_policy':
        # Schema models firmware exclusions under advanced_mode.
        # Map only the fields currently expected by the playbook.
        advanced = item.get('advanced_mode')
        if not isinstance(advanced, dict):
            advanced = item.get('advanced')

        if isinstance(advanced, dict):
            if 'exclude_storage_controllers' in advanced:
                result['exclude_storage_controllers'] = advanced['exclude_storage_controllers']
            if 'exclude_drives' in advanced:
                result['exclude_drives'] = advanced['exclude_drives']

        # Prevent schema-only fields from reaching module args.
        result.pop('advanced_mode', None)

        # Schema uses model_bundle_version entries with
        # firmware_version/server_models. The module expects
        # model_bundle_combo entries with bundle_version/model_family.
        combos = result.get('model_bundle_combo')
        if isinstance(combos, list):
            normalized_combos = []
            for combo in combos:
                if not isinstance(combo, dict):
                    continue

                new_combo = dict(combo)
                if 'bundle_version' not in new_combo and 'firmware_version' in combo:
                    new_combo['bundle_version'] = combo['firmware_version']

                if 'model_family' not in new_combo:
                    server_models = combo.get('server_models')
                    if isinstance(server_models, list) and server_models:
                        new_combo['model_family'] = server_models[0]

                new_combo.pop('firmware_version', None)
                new_combo.pop('server_models', None)
                normalized_combos.append(new_combo)

            result['model_bundle_combo'] = normalized_combos

    elif module_name == 'intersight_flow_control_policy':
        for direction_key in ('receive_direction', 'send_direction'):
            direction_value = result.get(direction_key)
            if isinstance(direction_value, str):
                result[direction_key] = direction_value.strip().lower()
        result.pop('advanced', None)

    elif module_name == 'intersight_ip_pool':
        # IPv4 blocks
        ipv4_blocks = result.get('ipv4_blocks')
        if isinstance(ipv4_blocks, list):
            processed_ipv4_blocks = _process_blocks_with_size(ipv4_blocks, 'from', drop_to=True)
            converted_ipv4_blocks = []
            for block in processed_ipv4_blocks:
                if not isinstance(block, dict):
                    converted_ipv4_blocks.append(block)
                    continue

                new_block = dict(block)
                gateway = new_block.get('gateway')
                if gateway not in (None, ''):
                    ipv4_config = {}
                    existing_ipv4_config = new_block.get('ipv4_config')
                    if isinstance(existing_ipv4_config, dict):
                        ipv4_config.update(existing_ipv4_config)

                    for key in ('gateway', 'netmask', 'primary_dns', 'secondary_dns'):
                        if key in new_block and new_block.get(key) not in (None, ''):
                            ipv4_config[key] = new_block.pop(key)

                    new_block['ipv4_config'] = ipv4_config

                converted_ipv4_blocks.append(new_block)

            result['ipv4_blocks'] = converted_ipv4_blocks
        # IPv6 blocks
        ipv6_blocks = result.get('ipv6_blocks')
        if isinstance(ipv6_blocks, list):
            processed_ipv6_blocks = _process_blocks_with_size(ipv6_blocks, 'from', drop_to=True)
            converted_ipv6_blocks = []
            for block in processed_ipv6_blocks:
                if not isinstance(block, dict):
                    converted_ipv6_blocks.append(block)
                    continue

                new_block = dict(block)
                gateway = new_block.get('gateway')
                if gateway not in (None, ''):
                    ipv6_config = {}
                    existing_ipv6_config = new_block.get('ipv6_config')
                    if isinstance(existing_ipv6_config, dict):
                        ipv6_config.update(existing_ipv6_config)

                    for key in ('gateway', 'prefix', 'primary_dns', 'secondary_dns'):
                        if key in new_block and new_block.get(key) not in (None, ''):
                            ipv6_config[key] = new_block.pop(key)

                    new_block['ipv6_config'] = ipv6_config

                converted_ipv6_blocks.append(new_block)

            result['ipv6_blocks'] = converted_ipv6_blocks

        # Module requires a global flag when subnet settings are defined per block.
        has_block_level_gateway = False
        for block_list_key in ('ipv4_blocks', 'ipv6_blocks'):
            block_list = result.get(block_list_key)
            if not isinstance(block_list, list):
                continue
            if any(
                isinstance(block, dict) and (
                    block.get('gateway') not in (None, '')
                    or (isinstance(block.get('ipv4_config'), dict)
                        and block['ipv4_config'].get('gateway') not in (None, ''))
                    or (isinstance(block.get('ipv6_config'), dict)
                        and block['ipv6_config'].get('gateway') not in (None, ''))
                )
                for block in block_list
            ):
                has_block_level_gateway = True
                break

        if has_block_level_gateway:
            result['enable_block_level_subnet_config'] = True

    elif module_name == 'intersight_iqn_pool':
        # Schema uses iqn_blocks[].from, module expects iqn_suffix_blocks[].iqn_from
        blocks = result.get('iqn_suffix_blocks')
        if isinstance(blocks, list):
            converted = []
            for block in blocks:
                if isinstance(block, dict):
                    new_block = dict(block)
                    # Rename from → iqn_from, calculate size if to is present
                    if 'from' in new_block:
                        size_calc = _calculate_size_from_range(new_block, 'from')
                        if size_calc:
                            new_block.update(size_calc)
                        new_block['iqn_from'] = new_block.pop('from')
                    new_block.pop('to', None)  # Drop 'to' after size calculation
                    converted.append(new_block)
                else:
                    converted.append(block)
            result['iqn_suffix_blocks'] = converted

    elif module_name == 'intersight_iscsi_boot_policy':
        # Module choices are lowercase; schema examples/defaults use title/upper.
        target_source_type = result.get('target_source_type')
        if isinstance(target_source_type, str):
            result['target_source_type'] = target_source_type.lower()

        initiator_ip_source = result.get('initiator_ip_source')
        if isinstance(initiator_ip_source, str):
            result['initiator_ip_source'] = initiator_ip_source.lower()

        static_ipv4 = item.get('initiator_static_ipv4_config')
        if isinstance(static_ipv4, dict):
            if 'ip_address' in static_ipv4:
                result['initiator_static_ipv4_address'] = static_ipv4['ip_address']
            if 'netmask' in static_ipv4:
                result['initiator_static_ipv4_netmask'] = static_ipv4['netmask']
            if 'gateway' in static_ipv4:
                result['initiator_static_ipv4_gateway'] = static_ipv4['gateway']
            if 'primary_dns' in static_ipv4:
                result['initiator_static_ipv4_primary_dns'] = static_ipv4['primary_dns']
            if 'secondary_dns' in static_ipv4:
                result['initiator_static_ipv4_secondary_dns'] = static_ipv4['secondary_dns']

        # Map schema auth fields to module-native chap/mutual_chap dictionaries.
        # Password is a Sensitive Variable Identifier (integer), resolve from environment.
        auth_mode = item.get('authentication')
        username = item.get('username')
        password_var_id = item.get('password')
        
        # Resolve password from environment variable based on variable ID
        password_value = None
        if isinstance(password_var_id, int) and password_var_id > 0:
            # Environment variable format: iscsi_boot_password_<id>
            env_var_name = f'iscsi_boot_password_{password_var_id}'
            password_value = os.environ.get(env_var_name)
        
        if isinstance(auth_mode, str):
            mode = auth_mode.lower()
            if mode == 'chap' and username not in (None, '') and password_value not in (None, ''):
                result['chap'] = {
                    'user_id': str(username),
                    'password': str(password_value),
                }
            elif mode == 'mutual_chap' and username not in (None, '') and password_value not in (None, ''):
                # Schema only provides one credential pair, so apply it to both
                # initiator and target auth profiles.
                creds = {
                    'user_id': str(username),
                    'password': str(password_value),
                }
                result['chap'] = dict(creds)
                result['mutual_chap'] = dict(creds)

        # Prevent unsupported key from reaching module args.
        result.pop('initiator_static_ipv4_config', None)
        result.pop('authentication', None)
        result.pop('username', None)
        result.pop('password', None)

    elif module_name == 'intersight_iscsi_static_target_policy':
        ip_address = item.get('ip_address')
        ip_protocol = result.get('ip_protocol')
        if isinstance(ip_protocol, str):
            if ip_protocol == 'IPv4' and ip_address is not None:
                result['ipv4_address'] = ip_address
            elif ip_protocol == 'IPv6' and ip_address is not None:
                result['ipv6_address'] = ip_address

    elif module_name == 'intersight_lan_connectivity_policy':
        vnics = item.get('vnics', [])
        if isinstance(vnics, list):
            result['vnics'] = _expand_lcp_vnics(vnics, item.get('vnic_placement_mode'))

    elif module_name == 'intersight_local_user_policy':
        # Expand password_properties sub-dict into flat module params
        pp = item.get('password_properties', {})
        if isinstance(pp, dict):
            for sub_key in ('enforce_strong_password', 'enable_password_expiry',
                            'password_history'):
                if sub_key in pp and sub_key not in result:
                    result[sub_key] = pp[sub_key]

    elif module_name == 'intersight_mac_pool':
        blocks = result.get('mac_blocks')
        if isinstance(blocks, list):
            processed_blocks = _process_blocks_with_size(blocks, 'from', drop_to=True)
            remapped_blocks = []
            for block in processed_blocks:
                if not isinstance(block, dict):
                    remapped_blocks.append(block)
                    continue
                new_block = dict(block)
                if 'from' in new_block and 'address_from' not in new_block:
                    new_block['address_from'] = new_block.pop('from')
                remapped_blocks.append(new_block)
            result['mac_blocks'] = remapped_blocks

    elif module_name == 'intersight_network_connectivity_policy':
        # dns_servers_v4 list → preferred / alternate IPv4 DNS params
        v4 = item.get('dns_servers_v4', [])
        if isinstance(v4, list):
            if len(v4) > 0 and 'preferred_ipv4_dns_server' not in result:
                result['preferred_ipv4_dns_server'] = v4[0]
            if len(v4) > 1 and 'alternate_ipv4_dns_server' not in result:
                result['alternate_ipv4_dns_server'] = v4[1]
        # dns_servers_v6 list → preferred / alternate IPv6 DNS params
        v6 = item.get('dns_servers_v6', [])
        if isinstance(v6, list):
            if len(v6) > 0 and 'preferred_ipv6_dns_server' not in result:
                result['preferred_ipv6_dns_server'] = v6[0]
            if len(v6) > 1 and 'alternate_ipv6_dns_server' not in result:
                result['alternate_ipv6_dns_server'] = v6[1]

    elif module_name == 'intersight_port_policy':
        # Convert schema port_modes[] into module params:
        # - entries with Breakout* custom_mode => breakout_ports[]
        # - FibreChannel custom_mode => fc_port_mode dict
        port_modes = item.get('port_modes', [])
        if isinstance(port_modes, list):
            breakout_ports = []
            fc_port_mode = None
            for mode in port_modes:
                if not isinstance(mode, dict):
                    continue
                custom_mode = mode.get('custom_mode')
                port_list = mode.get('port_list', [])
                mode_state = mode.get('state', 'present')
                if not isinstance(port_list, list) or len(port_list) == 0:
                    continue

                if isinstance(custom_mode, str) and 'Breakout' in custom_mode:
                    if len(port_list) > 1:
                        start_port = port_list[0]
                        end_port = port_list[1]
                        if isinstance(start_port, int) and isinstance(end_port, int):
                            step = 1 if end_port >= start_port else -1
                            for port_id in range(start_port, end_port + step, step):
                                breakout_ports.append({
                                    'port_id': port_id,
                                    'custom_mode': custom_mode,
                                    'state': mode_state,
                                })
                    else:
                        breakout_ports.append({
                            'port_id': port_list[0],
                            'custom_mode': custom_mode,
                            'state': mode_state,
                        })
                else:
                    if len(port_list) > 1:
                        start_port = port_list[0]
                        end_port = port_list[1]
                    else:
                        start_port = port_list[0]
                        end_port = port_list[0]
                    fc_port_mode = {
                        'port_id_start': start_port,
                        'port_id_end': end_port,
                        'state': mode_state,
                    }

            if breakout_ports and 'breakout_ports' not in result:
                result['breakout_ports'] = breakout_ports
            if fc_port_mode and 'fc_port_mode' not in result:
                result['fc_port_mode'] = fc_port_mode

    elif module_name == 'intersight_san_connectivity_policy':
        vhbas = item.get('vhbas', [])
        if isinstance(vhbas, list):
            result['vhbas'] = _expand_scp_vhbas(vhbas)

    elif module_name == 'intersight_syslog_policy':
        # local_logging.minimum_severity → local_logging_minimum_severity
        ll = item.get('local_logging', {})
        if isinstance(ll, dict) and 'local_logging_minimum_severity' not in result:
            if 'minimum_severity' in ll:
                result['local_logging_minimum_severity'] = ll['minimum_severity']
        # remote_logging list → first / second remote logging params
        rl = item.get('remote_logging', [])
        if isinstance(rl, list):
            for idx, entry in enumerate(rl[:2]):
                prefix = 'first_' if idx == 0 else 'second_'
                for sub_key in ('enabled', 'hostname', 'minimum_severity', 'port', 'protocol'):
                    module_param = f'{prefix}remote_logging_{sub_key}'
                    if sub_key in entry and module_param not in result:
                        result[module_param] = entry[sub_key]

    elif module_name == 'intersight_virtual_media_policy':
        add_virtual_media = item.get('add_virtual_media', [])
        if isinstance(add_virtual_media, list):
            for mapping in add_virtual_media:
                if not isinstance(mapping, dict):
                    continue

                media_type = mapping.get('type')
                if media_type in (None, ''):
                    media_type = mapping.get('device_type')
                if not isinstance(media_type, str):
                    media_type = 'cdd'
                media_type = media_type.strip().lower()
                if media_type not in ('cdd', 'hdd'):
                    media_type = 'cdd'

                # Module supports one dictionary per media type.
                target_key = 'cdd_virtual_media' if media_type == 'cdd' else 'hdd_virtual_media'
                if target_key in result:
                    continue

                result[target_key] = dict(mapping)

        # Prevent schema-only field from reaching module args.
        result.pop('add_virtual_media', None)

    elif module_name == 'intersight_vnic_template':
        # Module currently accepts a single network-group policy name.
        ng_policy = result.get('fabric_eth_network_group_policy_name')
        if isinstance(ng_policy, list):
            if len(ng_policy) > 0:
                result['fabric_eth_network_group_policy_name'] = ng_policy[0]
            else:
                result.pop('fabric_eth_network_group_policy_name', None)

        sriov_settings = result.get('sriov_settings')
        if isinstance(sriov_settings, dict):
            mapped_sriov = {}
            sriov_key_map = {
                'completion_queue_count_per_vf': 'comp_count_per_vf',
                'interrupt_count_per_vf': 'int_count_per_vf',
                'number_of_vfs': 'vf_count',
                'receive_queue_count_per_vf': 'rx_count_per_vf',
                'transmit_queue_count_per_vf': 'tx_count_per_vf',
                'enabled': 'enabled',
            }
            for src_key, dst_key in sriov_key_map.items():
                if src_key in sriov_settings and sriov_settings[src_key] not in (None, ''):
                    mapped_sriov[dst_key] = sriov_settings[src_key]
            result['sriov_settings'] = mapped_sriov

        usnic_settings = result.get('usnic_settings')
        if isinstance(usnic_settings, dict):
            mapped_usnic = {}
            usnic_key_map = {
                'class_of_service': 'cos',
                'number_of_usnics': 'count',
                'usnic_adapter_policy': 'usnic_adapter_policy_name',
            }
            for src_key, dst_key in usnic_key_map.items():
                if src_key in usnic_settings and usnic_settings[src_key] not in (None, ''):
                    mapped_usnic[dst_key] = usnic_settings[src_key]
            result['usnic_settings'] = mapped_usnic

        vmq_settings = result.get('vmq_settings')
        if isinstance(vmq_settings, dict):
            mapped_vmq = {}
            vmq_key_map = {
                'enable_virtual_machine_multi_queue': 'multi_queue_support',
                'enabled': 'enabled',
                'number_of_interrupts': 'num_interrupts',
                'number_of_sub_vnics': 'num_sub_vnics',
                'number_of_virtual_machine_queues': 'num_vmqs',
                'vmmq_adapter_policy': 'vmmq_adapter_policy_name',
            }
            for src_key, dst_key in vmq_key_map.items():
                if src_key in vmq_settings and vmq_settings[src_key] not in (None, ''):
                    mapped_vmq[dst_key] = vmq_settings[src_key]
            result['vmq_settings'] = mapped_vmq

        # Infer connection type from enabled connection settings if not explicit.
        if 'connection_type' not in result:
            if isinstance(result.get('sriov_settings'), dict) and result['sriov_settings'].get('enabled'):
                result['connection_type'] = 'sriov'
            elif isinstance(result.get('vmq_settings'), dict) and result['vmq_settings'].get('enabled'):
                result['connection_type'] = 'vmq'
            elif isinstance(result.get('usnic_settings'), dict) and (
                result['usnic_settings'].get('count', 0) not in (None, 0)
                or result['usnic_settings'].get('usnic_adapter_policy_name') not in (None, '')
            ):
                result['connection_type'] = 'usnic'
            else:
                result['connection_type'] = 'none'

    elif module_name == 'intersight_uuid_pool':
        blocks = result.get('uuid_suffix_blocks')
        if isinstance(blocks, list):
            result['uuid_suffix_blocks'] = _process_blocks_with_size(blocks, 'from', drop_to=True)

    elif module_name == 'intersight_wwn_pool':
        # Schema id_blocks[].from maps to module id_blocks[].wwn_from, calculate size from to if present
        blocks = result.get('id_blocks')
        if isinstance(blocks, list):
            converted = []
            for block in blocks:
                if isinstance(block, dict):
                    new_block = dict(block)
                    # Rename from → wwn_from, calculate size if to is present
                    if 'from' in new_block:
                        size_calc = _calculate_size_from_range(new_block, 'from')
                        if size_calc:
                            new_block.update(size_calc)
                        new_block['wwn_from'] = new_block.pop('from')
                    new_block.pop('to', None)  # Drop 'to' after size calculation
                    converted.append(new_block)
                else:
                    converted.append(block)
            result['id_blocks'] = converted

    # ---- Prune modules with strict param sets --------------------------------
    valid = _MODULE_VALID_PARAMS.get(module_name)
    if valid:
        result = {k: v for k, v in result.items()
                  if k in valid or k in _UNIVERSAL_KEYS}

    return result


class FilterModule:
    """Ansible filter module: schema default merging and module param mapping."""

    def filters(self):
        return {
            'merge_schema_defaults': merge_schema_defaults,
            'to_module_params': to_module_params,
            'split_port_policies': split_port_policies,
        }
