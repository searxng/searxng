# Security Policy

We love responsible reports of (potential) security issues in Zhensa.

You can contact us at security@zhensa.org.

Be sure to provide as much information as possible and if found
also reproduction steps of the identified vulnerability. Also
add the specific URL of the project as well as code you found
the issue in to your report.

## Defense-in-Depth Security Layers

Zhensa implements a multi-layered security approach known as Defense-in-Depth, which creates multiple security barriers to protect against threats. The main layers include:

### Application Security
- Directly secures code and software logic.
- Examples: Input validation (ensuring user input is correct), secure coding practices, and preventing common vulnerabilities like SQL injection.

### Data Security
- Protects sensitive information wherever it resides.
- Examples: Encrypting data at rest and in transit, and implementing access controls to limit data access to authorized personnel only.

### Authentication and Authorization
- Ensures only legitimate users can access systems and perform only permitted actions.
- Examples: Strong password policies, Two-Factor Authentication (2FA), and adhering to the Principle of Least Privilege.

### Network Security
- Secures network traffic accessing the application and data.
- Examples: Firewalls, Intrusion Detection Systems (IDS), and network segmentation.

### Host / Operating System Security
- Secures the servers or devices running the code.
- Examples: Regular OS patching, disabling unnecessary services, and hardening server configurations.

### Physical Security
- Protects physical locations like data centers or server rooms.
- Examples: Locks and access cards on doors, CCTV cameras, and measures to prevent unauthorized access.

### Human Layer
- Focuses on people, often the most critical and vulnerable layer.
- Examples: Employee training to recognize phishing and social engineering attacks, and enforcing security policies.

These layers work together to build a robust security framework. For code-focused efforts, Application Security and Data Security are particularly important.
