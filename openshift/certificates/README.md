# Manage Certificates for the OpenShift cluster

## Table of Content

  * [Prerequisites](#prerequisites): Preparing the certificate files
  * [Create the API Certificate Request](#create-the-api-certificate-request): Generate CSR for API.
  * [Create the Ingress Gateway Certificate Request](#create-the-ingress-gateway-certificate-request): Generate CSR for Ingress Gateway.
  * [Run the Certificate Modules](#run-the-certificate-modules): Import User Certificate trusted sources.
  * [Manually Add API Certificate](#manually-add-api-certificate)`: Replace API self-signed certificate with signed certificate.
  * [Manually Add Ingress Gateway Certificate](#manually-add-ingress-gateway-certificate)`: Replace Ingress Gateway self-signed certificate with signed certificate.

## Prerequisites

* You must have a wildcard certificate for the fully qualified .`apps` subdomain and its corresponding private key. Each should be in a separate PEM format file.
* The private key must be unencrypted. If your key is encrypted, decrypt it before importing it into OpenShift Container Platform.
* The certificate must include the subjectAltName extension showing `*.apps.<clustername>.<domain>`.
* The certificate file can contain one or more certificates in a chain. The file must list the wildcard certificate as the first certificate, followed by other intermediate certificates, and then ending with the root CA certificate.
* Copy the root CA certificate into an additional PEM format file.
* Verify that all certificates include `-----END CERTIFICATE-----` also end with one carriage return after that line.

## Create the API Certificate Request

### Components of a Distinguished Name

The key-value pairs in a distinguished name use standard abbreviations: 

  * `C`: Country Name (2-letter ISO code, e.g., `US`)
  * `ST`: State or Province Name (full name, e.g., `California`)
  * `L`: Locality Name (e.g., `San Francisco` or `SomeCity`)
  * `O`: Organization Name (e.g., `My Company`)
  * `OU`: Organizational Unit Name (e.g., `IT Department` or `MyDivision`)
  * `CN`: Common Name (typically the Fully Qualified Domain Name (FQDN) of the server, e.g.,` www.example.com`)
  * `emailAddress`: Contact email address (e.g., `webmaster@example.com`)

1. Create the OpenSSL Configuration file `api.conf`.  Example Below:

```bash
[req]
default_bits = 2048
prompt = no
default_md = sha512
req_extensions = v3_req
distinguished_name = req_distinguished_name

[req_distinguished_name]
C = UCS
ST = California
L = San Jose
O = Example Company
OU = AI Admins
CN = api.<cluster-name>.example.com
emailAddress = admins@example.com

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = api.<cluster-name>.example.com
IP.1 = 198.18.0.10
```

2. Run OpenSSL to create the signing request.

```bash
openssl req -newkey rsa:2048 -keyout api-<cluster-name>.key -out api-<cluster-name>.csr -config api.conf -nodes
```

3. Submit the request to your certificate authority

### [Back to Table of Content](#table-of-content)

## Create the Ingress Gateway Certificate Request

### Components of a Distinguished Name

1. Create the OpenSSL Configuration file `ingress.conf`.  Example Below:

```bash
[req]
default_bits = 2048
prompt = no
default_md = sha512
req_extensions = v3_req
distinguished_name = req_distinguished_name

[req_distinguished_name]
C = UCS
ST = California
L = San Jose
O = Example Company
OU = AI Admins
CN = apps.<cluster-name>.example.com
emailAddress = admins@example.com

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = apps.<cluster-name>.example.com
DNS.2 = *.apps.<cluster-name>.example.com
IP.1 = 198.18.0.11
```

2. Run OpenSSL to create the signing request.

```bash
openssl req -newkey rsa:2048 -keyout apps-<cluster-name>.key -out apps-<cluster-name>.csr -config ingress.conf -nodes
```

3. Submit the request to your certificate authority

### [Back to Table of Content](#table-of-content)

## Run the Certificate Modules

### Load the Variables to Environment

Obtain the API token and url by logging into OpenShift > User > Copy Login

![Copy Login Command](../../images/copy_login_command.png)

![Display Token](../../images/display_token.png)

* The `user_ca_bundle_file` should only include the Root CA for the API and Ingress Certificates.  If they include a intermediatory certificate, do not include.
* The `api_cert_chain_file` should include the certificate, intermediatory if used, and root certificate in PEM format.
* The `api_key_file` should include the api key file in unencrypted PEM format.
* The `ingress_cert_chain_file` should include the certificate, intermediatory if used, and root certificate in PEM format.
* The `ingress_key_file` should include the api key file in unencrypted PEM format.

```bash
export openshift_api_url="api_url"
export openshift_token_id="token_value"
export api_cert_chain_file="full_path_to_api_cert_chain_file"
export api_key_file="full_path_to_api_key_file"
export api_server_hostname="api-server-hostname"
export ingress_cert_chain_file="full_path_to_ingress_cert_chain_file"
export ingress_key_file="full_path_to_ingress_key_file"
export user_ca_bundle_file="full_path_to_bundle_file"
```

[Red Hat Documentation - Configuring Certificates](https://docs.redhat.com/en/documentation/openshift_container_platform/4.8/html/security_and_compliance/configuring-certificates)

### How to Run

1. Run the User CA Bundle playbook:

```bash
ansible-playbook load_user_bundle_ca.yaml
```

2. Verify the ConfigMap was created as expected:

```bash
oc get configmap user-ca-bundle -n openshift-config -o yaml
```

3. Run the Ingress Certificate playbook:

```bash
ansible-playbook load_ingress_certificate.yaml
```

4. If success the consle WebUI should load with the new certificate.

5. Run the User API Certificate playbook:

```bash
ansible-playbook load_api_certificate.yaml
```

5. Verify the Kube API Server is ready:

```bash
oc get clusteroperators kube-apiserver
```

* Example Output.  It is complete when the `AVAILABLE` column shows `True`.

```bash
$ oc get clusteroperators kube-apiserver
NAME             VERSION   AVAILABLE   PROGRESSING   DEGRADED   SINCE   MESSAGE
kube-apiserver   4.20.15   True        True          False      8d      NodeInstallerProgressing: 1 node is at revision 9; 2 nodes are at revision 10
$ oc get clusteroperators kube-apiserver
NAME             VERSION   AVAILABLE   PROGRESSING   DEGRADED   SINCE   MESSAGE
kube-apiserver   4.20.15   True        False         False      8d      
$
```

6. If success the API should load with the new certificate:

* https://api.<cluster-name>.<base-domain>:6443

### Complete

### [Back to Table of Content](#table-of-content)

## Manually Add API Certificate

1. Log in to the cluster with an account having administrator privileges.

2. Create a Secret in the `openshift-config` namespace that contains the certificate chain and private key:

```bash
oc create secret tls <secret-name> \
  --cert=</path/to/cert.crt.fullchain> \
  --key=</path/to/cert.key> \
  -n openshift-config
```

* Replace `<secret-name>` with a name for your new secret.
* Replace `</path/to/cert.crt.fullchain>` and `</path/to/cert.key>` with the paths to your certificate chain and key files.

3. Confirm the secret was created.

```bash
oc -n openshift-config get secret
```

4. Update the API server to reference the created secret using the `apiserver/cluster` custom resource:

```bash
oc patch apiserver cluster --type=merge -p '{"spec":{"servingCerts": {"namedCertificates": [{"names": ["<api-server-hostname>"], "servingCertificate": {"name": "<secret>"}}]}}}'
```

* Replace `<api-server-hostname>` with the external hostname clients use to reach the API server.
* Replace `<secret-name>` with the name you used for the secret in the previous step.
* IMPORTANT: Do not provide a named certificate for the internal load balancer hostname (`api-int.<cluster_name>.<base_domain>`) as this can leave the cluster in a degraded state.

4. Verify the configuration change by examining the `apiserver/cluster` object:

```bash
oc get apiserver cluster -o yaml
```
5. Check the kube-apiserver operator, and verify that a new revision of the Kubernetes API server rolls out. It may take a minute for the operator to detect the configuration change and trigger a new deployment. While the new revision is rolling out, PROGRESSING will report True.

```bash
oc get clusteroperators kube-apiserver
```

* Example Output.  It is complete when the `AVAILABLE` column shows `True`.

```bash
$ oc get clusteroperators kube-apiserver
NAME             VERSION   AVAILABLE   PROGRESSING   DEGRADED   SINCE   MESSAGE
kube-apiserver   4.20.15   True        True          False      8d      NodeInstallerProgressing: 1 node is at revision 9; 2 nodes are at revision 10
$ oc get clusteroperators kube-apiserver
NAME             VERSION   AVAILABLE   PROGRESSING   DEGRADED   SINCE   MESSAGE
kube-apiserver   4.20.15   True        False         False      8d      
$
```

## Manually Add Ingress Gateway Certificate

### Prerequisites

You need the following files in PEM format:

* `cert.crt.fullchain`: The server certificate file, including all intermediate and root CA certificates in order.
* `cert.key`: The unencrypted private key that corresponds to the server certificate. 


### Procedure

1. **Create a Kubernetes TLS Secret**: Run the following command in the openshift-ingress namespace, referencing your certificate and key files:

```bash
oc create secret tls <secret-name> \
  --cert=</path/to/cert.crt.fullchain> \
  --key=</path/to/cert.key> \
  -n openshift-ingress
```

2. **Update the Ingress Controller**: Apply a patch to the default ingress controller to utilize the newly created secret, as detailed in the Red Hat documentation:

```bash
oc patch ingresscontroller.operator/default --type=merge -p '{"spec":{"defaultCertificate": {"name": "<secret-name>"}}}' -n openshift-ingress-operator
```

3. **Verify the Update**: Monitor the router pod logs to confirm the changes are applied:

```bash
oc get events -w -n openshift-ingress
```

## Sources

[Custom Root CA in OpenShift](https://kenmoini.com/post/2022/02/custom-root-ca-in-openshift/)
[Red Hat Support - Custom PKI](https://access.redhat.com/documentation/en-us/openshift_container_platform/4.9/html/networking/configuring-a-custom-pki)

### [Back to Table of Content](#table-of-content)
