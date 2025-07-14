Deployment
==========

This guide provides comprehensive instructions for deploying the EGen Platform in various environments, from development setups to production-grade enterprise deployments.

Deployment Options
----------------

The EGen Platform supports multiple deployment options to suit different needs:

Local Development
~~~~~~~~~~~~~~~

For development and testing purposes, you can run the platform locally:

.. code-block:: bash

   # Clone the repository
   git clone https://github.com/egen-platform/egen.git
   cd egen
   
   # Install dependencies
   pip install -e .
   
   # Run the development server
   python -m egen.api.main --dev

This will start the API server on http://localhost:8000 with hot-reloading enabled.

Docker Deployment
~~~~~~~~~~~~~~~

For containerized deployments, we provide Docker and Docker Compose configurations:

.. code-block:: bash

   # Build and start all services
   docker-compose up -d
   
   # View logs
   docker-compose logs -f
   
   # Stop all services
   docker-compose down

The Docker Compose setup includes:

1. API server
2. Web interface
3. Redis for caching
4. PostgreSQL for persistent storage
5. Prometheus and Grafana for monitoring

Custom Docker Compose configuration:

.. code-block:: yaml

   # docker-compose.custom.yml
   version: '3.8'
   
   services:
     api:
       image: egen/api:latest
       ports:
         - "8000:8000"
       environment:
         - EGEN_ENV=production
         - EGEN_DB_URI=postgresql://user:password@db:5432/egen
         - EGEN_REDIS_URI=redis://redis:6379/0
       volumes:
         - ./models:/app/models
         - ./config:/app/config
       depends_on:
         - db
         - redis
   
     web:
       image: egen/web:latest
       ports:
         - "8501:8501"
       environment:
         - EGEN_API_URL=http://api:8000
       depends_on:
         - api
   
     # Database
     db:
       image: postgres:14
       volumes:
         - postgres_data:/var/lib/postgresql/data
       environment:
         - POSTGRES_USER=user
         - POSTGRES_PASSWORD=password
         - POSTGRES_DB=egen
   
     # Cache
     redis:
       image: redis:7
       volumes:
         - redis_data:/data
   
   volumes:
     postgres_data:
     redis_data:

Kubernetes Deployment
~~~~~~~~~~~~~~~~~~

For production environments, we recommend Kubernetes deployment:

.. code-block:: bash

   # Apply Kubernetes manifests
   kubectl apply -f k8s/
   
   # Check deployment status
   kubectl get pods
   
   # Access the service
   kubectl port-forward svc/egen-api 8000:8000

Key Kubernetes resources include:

1. Deployments for API and web services
2. StatefulSets for databases
3. Services for networking
4. ConfigMaps and Secrets for configuration
5. Ingress for external access
6. HorizontalPodAutoscalers for scaling

Example Kubernetes deployment manifest:

.. code-block:: yaml

   # k8s/api-deployment.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: egen-api
     labels:
       app: egen
       component: api
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: egen
         component: api
     template:
       metadata:
         labels:
           app: egen
           component: api
       spec:
         containers:
         - name: api
           image: egen/api:latest
           ports:
           - containerPort: 8000
           resources:
             requests:
               memory: "1Gi"
               cpu: "500m"
             limits:
               memory: "2Gi"
               cpu: "1000m"
           env:
           - name: EGEN_ENV
             value: "production"
           - name: EGEN_DB_URI
             valueFrom:
               secretKeyRef:
                 name: egen-secrets
                 key: db_uri
           volumeMounts:
           - name: config-volume
             mountPath: /app/config
           - name: models-volume
             mountPath: /app/models
         volumes:
         - name: config-volume
           configMap:
             name: egen-config
         - name: models-volume
           persistentVolumeClaim:
             claimName: models-pvc

Cloud Provider Deployments
~~~~~~~~~~~~~~~~~~~~~~~

The EGen Platform can be deployed on major cloud providers:

AWS Deployment
^^^^^^^^^^^^^

For AWS deployments, we recommend using ECS or EKS:

**ECS Deployment**:

1. Create an ECS cluster
2. Define task definitions for each service
3. Create services with appropriate networking
4. Set up an Application Load Balancer
5. Configure auto-scaling

**EKS Deployment**:

1. Create an EKS cluster
2. Apply Kubernetes manifests
3. Set up AWS Load Balancer Controller
4. Configure IAM roles for service accounts
5. Set up CloudWatch for monitoring

Azure Deployment
^^^^^^^^^^^^^^^

For Azure deployments, we recommend using AKS:

1. Create an AKS cluster
2. Apply Kubernetes manifests
3. Set up Azure Application Gateway
4. Configure Azure Monitor
5. Set up Azure Key Vault for secrets

GCP Deployment
^^^^^^^^^^^^^

For GCP deployments, we recommend using GKE:

1. Create a GKE cluster
2. Apply Kubernetes manifests
3. Set up Cloud Load Balancing
4. Configure Cloud Monitoring
5. Set up Secret Manager for secrets

System Requirements
-----------------

Minimum Requirements
~~~~~~~~~~~~~~~~~

For basic deployment (inference only):

* **CPU**: 8 cores
* **RAM**: 16 GB
* **Storage**: 50 GB SSD
* **GPU**: NVIDIA GPU with 8+ GB VRAM (for model inference)
* **Network**: 100 Mbps
* **Operating System**: Ubuntu 20.04+ or similar Linux distribution

Recommended Requirements
~~~~~~~~~~~~~~~~~~~~

For production deployment with all features:

* **CPU**: 16+ cores
* **RAM**: 64+ GB
* **Storage**: 500+ GB SSD
* **GPU**: NVIDIA A100, A10G, or similar (for model training and inference)
* **Network**: 1+ Gbps
* **Operating System**: Ubuntu 22.04 LTS

Scaling Considerations
~~~~~~~~~~~~~~~~~~~

The EGen Platform can scale horizontally for increased load:

* **API Servers**: Add more replicas for increased request handling
* **Model Servers**: Add more GPU instances for parallel inference
* **Database**: Use replication and sharding for increased data load
* **Cache**: Distribute Redis across multiple nodes

Configuration
------------

Environment Variables
~~~~~~~~~~~~~~~~~~

The platform can be configured using environment variables:

.. code-block:: bash

   # Core settings
   EGEN_ENV=production  # production, development, testing
   EGEN_LOG_LEVEL=info  # debug, info, warning, error
   EGEN_SECRET_KEY=your-secret-key
   
   # Database settings
   EGEN_DB_URI=postgresql://user:password@localhost:5432/egen
   
   # Redis settings
   EGEN_REDIS_URI=redis://localhost:6379/0
   
   # Model settings
   EGEN_MODEL_PATH=/path/to/models
   EGEN_DEFAULT_MODEL=THL-150
   
   # API settings
   EGEN_API_HOST=0.0.0.0
   EGEN_API_PORT=8000
   EGEN_API_WORKERS=4
   
   # Web settings
   EGEN_WEB_PORT=8501
   
   # Security settings
   EGEN_ENABLE_AUTH=true
   EGEN_AUTH_PROVIDER=jwt  # jwt, oauth, api_key
   EGEN_CORS_ORIGINS=http://localhost:3000,https://example.com

Configuration Files
~~~~~~~~~~~~~~~~~

For more complex configurations, use YAML configuration files:

.. code-block:: yaml

   # config/egen.yml
   environment: production
   
   logging:
     level: info
     format: json
     output: stdout
     file: /var/log/egen/api.log
   
   database:
     uri: postgresql://user:password@localhost:5432/egen
     pool_size: 10
     max_overflow: 20
     pool_timeout: 30
   
   redis:
     uri: redis://localhost:6379/0
     pool_size: 10
   
   model:
     path: /path/to/models
     default: THL-150
     quantization: int8
     batch_size: 4
     max_length: 2048
   
   api:
     host: 0.0.0.0
     port: 8000
     workers: 4
     timeout: 60
     rate_limit: 100
   
   web:
     port: 8501
     theme: light
   
   security:
     enable_auth: true
     auth_provider: jwt
     secret_key: your-secret-key
     token_expiry: 86400
     cors_origins:
       - http://localhost:3000
       - https://example.com

Load the configuration in your application:

.. code-block:: python

   from egen.config import load_config
   
   config = load_config("/path/to/config/egen.yml")
   db_uri = config.database.uri

Securing Your Deployment
---------------------

TLS/SSL Configuration
~~~~~~~~~~~~~~~~~~

Always use TLS/SSL in production:

**Nginx Configuration**:

.. code-block:: nginx

   server {
       listen 443 ssl;
       server_name api.egen-platform.org;
       
       ssl_certificate /path/to/fullchain.pem;
       ssl_certificate_key /path/to/privkey.pem;
       ssl_protocols TLSv1.2 TLSv1.3;
       ssl_ciphers HIGH:!aNULL:!MD5;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }

**Let's Encrypt with Certbot**:

.. code-block:: bash

   # Install Certbot
   apt-get update
   apt-get install certbot python3-certbot-nginx
   
   # Obtain and install certificate
   certbot --nginx -d api.egen-platform.org

Firewall Configuration
~~~~~~~~~~~~~~~~~~~

Secure your deployment with proper firewall rules:

**UFW (Uncomplicated Firewall)**:

.. code-block:: bash

   # Allow SSH
   ufw allow 22/tcp
   
   # Allow HTTPS
   ufw allow 443/tcp
   
   # Enable firewall
   ufw enable
   
   # Check status
   ufw status

**Cloud Provider Security Groups**:

Configure security groups to allow only necessary traffic:

1. SSH (port 22) from trusted IPs only
2. HTTPS (port 443) from anywhere
3. Application-specific ports only from internal networks

Secret Management
~~~~~~~~~~~~~~~

Securely manage secrets in production:

**Using Environment Variables**:

.. code-block:: bash

   # Set secrets in environment
   export EGEN_SECRET_KEY="your-secret-key"
   export EGEN_DB_PASSWORD="your-db-password"
   
   # Start application
   python -m egen.api.main

**Using Docker Secrets**:

.. code-block:: yaml

   # docker-compose.yml
   version: '3.8'
   
   services:
     api:
       image: egen/api:latest
       secrets:
         - db_password
         - secret_key
       environment:
         - EGEN_DB_PASSWORD_FILE=/run/secrets/db_password
         - EGEN_SECRET_KEY_FILE=/run/secrets/secret_key
   
   secrets:
     db_password:
       file: ./secrets/db_password.txt
     secret_key:
       file: ./secrets/secret_key.txt

**Using Kubernetes Secrets**:

.. code-block:: yaml

   # Create secret
   apiVersion: v1
   kind: Secret
   metadata:
     name: egen-secrets
   type: Opaque
   data:
     db_password: base64-encoded-password
     secret_key: base64-encoded-key

Monitoring and Logging
--------------------

Prometheus and Grafana
~~~~~~~~~~~~~~~~~~~

Set up monitoring with Prometheus and Grafana:

.. code-block:: yaml

   # docker-compose.monitoring.yml
   version: '3.8'
   
   services:
     prometheus:
       image: prom/prometheus:latest
       volumes:
         - ./prometheus:/etc/prometheus
         - prometheus_data:/prometheus
       command:
         - '--config.file=/etc/prometheus/prometheus.yml'
       ports:
         - "9090:9090"
   
     grafana:
       image: grafana/grafana:latest
       volumes:
         - grafana_data:/var/lib/grafana
       environment:
         - GF_SECURITY_ADMIN_PASSWORD=admin_password
       ports:
         - "3000:3000"
       depends_on:
         - prometheus
   
   volumes:
     prometheus_data:
     grafana_data:

ELK Stack
~~~~~~~~

Set up centralized logging with the ELK stack:

.. code-block:: yaml

   # docker-compose.elk.yml
   version: '3.8'
   
   services:
     elasticsearch:
       image: docker.elastic.co/elasticsearch/elasticsearch:7.16.2
       environment:
         - discovery.type=single-node
       volumes:
         - elasticsearch_data:/usr/share/elasticsearch/data
       ports:
         - "9200:9200"
   
     logstash:
       image: docker.elastic.co/logstash/logstash:7.16.2
       volumes:
         - ./logstash/pipeline:/usr/share/logstash/pipeline
       ports:
         - "5000:5000"
       depends_on:
         - elasticsearch
   
     kibana:
       image: docker.elastic.co/kibana/kibana:7.16.2
       ports:
         - "5601:5601"
       depends_on:
         - elasticsearch
   
   volumes:
     elasticsearch_data:

Backup and Recovery
-----------------

Database Backup
~~~~~~~~~~~~~

Regularly back up your database:

.. code-block:: bash

   # PostgreSQL backup
   pg_dump -U user -d egen -h localhost -F c -f /backups/egen_$(date +%Y%m%d).dump
   
   # Automated daily backup with cron
   # Add to crontab:
   # 0 2 * * * pg_dump -U user -d egen -h localhost -F c -f /backups/egen_$(date +%Y%m%d).dump

Model Backup
~~~~~~~~~~

Back up your model files and configurations:

.. code-block:: bash

   # Create a tarball of model files
   tar -czf /backups/models_$(date +%Y%m%d).tar.gz /path/to/models
   
   # Copy to remote storage
   aws s3 cp /backups/models_$(date +%Y%m%d).tar.gz s3://egen-backups/models/

Disaster Recovery Plan
~~~~~~~~~~~~~~~~~~~

Prepare a disaster recovery plan:

1. **Regular Backups**: Automated daily backups
2. **Off-site Storage**: Store backups in multiple locations
3. **Recovery Testing**: Regularly test restoration procedures
4. **Documentation**: Maintain detailed recovery procedures
5. **Monitoring**: Set up alerts for backup failures

Example recovery procedure:

.. code-block:: bash

   # Restore PostgreSQL database
   pg_restore -U user -d egen -h localhost -c /backups/egen_20251015.dump
   
   # Restore model files
   mkdir -p /path/to/models
   tar -xzf /backups/models_20251015.tar.gz -C /

Upgrading
--------

Version Upgrade Process
~~~~~~~~~~~~~~~~~~~~

Follow these steps to upgrade the EGen Platform:

1. **Backup**: Create backups of database and configuration
2. **Download**: Get the new version
3. **Review**: Check release notes for breaking changes
4. **Test**: Test the upgrade in a staging environment
5. **Deploy**: Deploy the new version
6. **Verify**: Verify functionality after upgrade

Example upgrade process:

.. code-block:: bash

   # Backup current state
   pg_dump -U user -d egen -h localhost -F c -f /backups/egen_pre_upgrade.dump
   cp -r /path/to/config /backups/config_pre_upgrade
   
   # Stop current services
   docker-compose down
   
   # Pull new version
   docker-compose pull
   
   # Apply database migrations
   docker-compose run --rm api alembic upgrade head
   
   # Start new version
   docker-compose up -d
   
   # Verify functionality
   curl http://localhost:8000/v1/health

Rollback Procedure
~~~~~~~~~~~~~~~~

If an upgrade fails, follow these steps to rollback:

1. **Stop Services**: Stop all running services
2. **Restore Database**: Restore from pre-upgrade backup
3. **Restore Configuration**: Restore configuration files
4. **Deploy Previous Version**: Start the previous version
5. **Verify**: Verify functionality after rollback

Example rollback procedure:

.. code-block:: bash

   # Stop services
   docker-compose down
   
   # Restore database
   pg_restore -U user -d egen -h localhost -c /backups/egen_pre_upgrade.dump
   
   # Restore configuration
   cp -r /backups/config_pre_upgrade/* /path/to/config/
   
   # Start previous version
   docker-compose -f docker-compose.previous.yml up -d
   
   # Verify functionality
   curl http://localhost:8000/v1/health

Troubleshooting
-------------

Common Issues
~~~~~~~~~~~

**API Server Won't Start**

Check for:

1. Database connection issues
2. Port conflicts
3. Missing environment variables
4. Insufficient permissions

Solution:

.. code-block:: bash

   # Check logs
   docker-compose logs api
   
   # Verify database connection
   psql -U user -h localhost -d egen -c "SELECT 1;"
   
   # Check port availability
   netstat -tuln | grep 8000

**Model Loading Errors**

Check for:

1. Missing model files
2. Insufficient GPU memory
3. CUDA version mismatch
4. Incorrect model configuration

Solution:

.. code-block:: bash

   # Check model files
   ls -la /path/to/models
   
   # Check GPU status
   nvidia-smi
   
   # Verify CUDA version
   python -c "import torch; print(torch.version.cuda)"

**High Memory Usage**

Check for:

1. Too many concurrent requests
2. Memory leaks
3. Insufficient system resources
4. Large batch sizes

Solution:

.. code-block:: bash

   # Check memory usage
   free -h
   
   # Monitor process memory
   ps aux --sort=-%mem | head
   
   # Adjust batch size in configuration
   # Edit config/egen.yml
   # model.batch_size: 2  # Reduced from 4

Diagnostic Tools
~~~~~~~~~~~~~~

Use these tools for diagnosing issues:

.. code-block:: bash

   # Check system resources
   htop
   
   # Monitor network connections
   netstat -tuln
   
   # Check disk usage
   df -h
   
   # Monitor logs in real-time
   tail -f /var/log/egen/api.log
   
   # Check Docker container status
   docker stats

Performance Optimization
---------------------

API Performance
~~~~~~~~~~~~~

Optimize API performance with these techniques:

1. **Connection Pooling**: Configure database connection pools
2. **Caching**: Use Redis for caching frequent requests
3. **Asynchronous Processing**: Use background workers for long tasks
4. **Load Balancing**: Distribute traffic across multiple instances
5. **Rate Limiting**: Prevent abuse and ensure fair usage

Example API optimization configuration:

.. code-block:: yaml

   # config/egen.yml
   database:
     pool_size: 20
     max_overflow: 30
     pool_timeout: 30
   
   redis:
     pool_size: 20
   
   api:
     workers: 8
     timeout: 30
     rate_limit: 100
     max_connections: 1000

Model Inference Optimization
~~~~~~~~~~~~~~~~~~~~~~~~~

Optimize model inference performance:

1. **Quantization**: Use INT8 or FP16 quantization
2. **Batch Processing**: Process requests in batches
3. **Model Pruning**: Remove unnecessary weights
4. **GPU Optimization**: Use CUDA optimizations
5. **Caching**: Cache frequent responses

Example model optimization configuration:

.. code-block:: yaml

   # config/egen.yml
   model:
     quantization: int8  # or fp16
     batch_size: 4
     max_length: 1024
     cache_size: 1000
     use_cuda_graphs: true
     optimize_for_inference: true

Horizontal Scaling
~~~~~~~~~~~~~~~~

Scale horizontally for increased load:

1. **API Servers**: Add more replicas behind a load balancer
2. **Model Servers**: Distribute inference across multiple GPUs
3. **Database**: Use read replicas and sharding
4. **Cache**: Distribute Redis across multiple nodes
5. **Storage**: Use distributed file systems

Example Kubernetes horizontal scaling configuration:

.. code-block:: yaml

   # k8s/api-hpa.yaml
   apiVersion: autoscaling/v2
   kind: HorizontalPodAutoscaler
   metadata:
     name: egen-api-hpa
   spec:
     scaleTargetRef:
       apiVersion: apps/v1
       kind: Deployment
       name: egen-api
     minReplicas: 3
     maxReplicas: 10
     metrics:
     - type: Resource
       resource:
         name: cpu
         target:
           type: Utilization
           averageUtilization: 70

Advanced Deployment Scenarios
--------------------------

Multi-Region Deployment
~~~~~~~~~~~~~~~~~~~~

Deploy across multiple regions for high availability:

1. **Regional API Endpoints**: Deploy API servers in multiple regions
2. **Global Load Balancing**: Use DNS-based load balancing
3. **Data Replication**: Replicate databases across regions
4. **CDN Integration**: Use CDNs for static content
5. **Latency-Based Routing**: Route users to the nearest region

Example multi-region architecture:

.. code-block:: text

   User Request
       |
       v
   Global Load Balancer (Route 53, Cloud DNS)
       |
       +----------------+----------------+
       |                |                |
       v                v                v
   Region A         Region B         Region C
   (API + Model)    (API + Model)    (API + Model)
       |                |                |
       +----------------+----------------+
       |
       v
   Global Database (Aurora Global, Cosmos DB, Spanner)

Air-Gapped Deployment
~~~~~~~~~~~~~~~~~~

Deploy in air-gapped environments without internet access:

1. **Offline Installation**: Package all dependencies
2. **Local Model Storage**: Pre-download all models
3. **Local Documentation**: Include all documentation
4. **Update Process**: Define secure update procedures
5. **License Verification**: Offline license verification

Example air-gapped installation:

.. code-block:: bash

   # Create offline package
   python -m egen.tools.create_offline_package --output egen-offline.tar.gz
   
   # Transfer to air-gapped environment
   # (physical media or approved transfer mechanism)
   
   # Install in air-gapped environment
   tar -xzf egen-offline.tar.gz
   cd egen-offline
   ./install.sh

High-Security Deployment
~~~~~~~~~~~~~~~~~~~~~

Deploy with enhanced security for sensitive environments:

1. **Network Isolation**: Deploy in private subnets
2. **VPN Access**: Require VPN for all access
3. **Encryption**: Encrypt all data at rest and in transit
4. **Audit Logging**: Comprehensive audit trails
5. **Regular Security Scanning**: Automated vulnerability scanning

Example high-security deployment architecture:

.. code-block:: text

   Internet
       |
       v
   VPN Gateway
       |
       v
   Web Application Firewall
       |
       v
   Load Balancer (Private Subnet)
       |
       v
   API Servers (Private Subnet)
       |
       v
   Model Servers (Private Subnet)
       |
       v
   Database (Private Subnet)

Edge Deployment
~~~~~~~~~~~~~

Deploy on edge devices with limited resources:

1. **Model Optimization**: Use quantized and pruned models
2. **Minimal Dependencies**: Reduce dependency footprint
3. **Offline Operation**: Function without internet connection
4. **Resource Monitoring**: Monitor and limit resource usage
5. **Update Management**: Secure and efficient updates

Example edge deployment configuration:

.. code-block:: yaml

   # config/egen-edge.yml
   environment: edge
   
   model:
     path: /path/to/models
     default: THL-150-edge  # Edge-optimized model
     quantization: int8
     max_memory_usage: 2GB
     offline_mode: true
   
   api:
     host: 0.0.0.0
     port: 8000
     workers: 2
     timeout: 30
   
   logging:
     level: warning
     max_size: 100MB
     rotation: daily

Deployment Checklist
-----------------

Pre-Deployment
~~~~~~~~~~~~

1. **Requirements Analysis**: Determine hardware and software requirements
2. **Architecture Design**: Design deployment architecture
3. **Security Planning**: Plan security measures
4. **Backup Strategy**: Define backup and recovery procedures
5. **Monitoring Setup**: Plan monitoring and alerting

Deployment
~~~~~~~~~

1. **Environment Setup**: Prepare servers and infrastructure
2. **Installation**: Install the EGen Platform
3. **Configuration**: Configure for the specific environment
4. **Security Implementation**: Implement security measures
5. **Testing**: Test functionality and performance

Post-Deployment
~~~~~~~~~~~~~

1. **Monitoring**: Set up monitoring and alerting
2. **Documentation**: Document the deployment
3. **Training**: Train administrators and users
4. **Backup Verification**: Test backup and recovery
5. **Performance Tuning**: Optimize performance

Maintenance
~~~~~~~~~

1. **Regular Updates**: Keep the platform updated
2. **Security Patching**: Apply security patches
3. **Performance Monitoring**: Monitor and optimize performance
4. **Backup Execution**: Perform regular backups
5. **Capacity Planning**: Plan for future growth

Resources
--------

Documentation
~~~~~~~~~~~

* **Installation Guide**: Detailed installation instructions
* **Configuration Reference**: Complete configuration options
* **API Documentation**: API endpoints and usage
* **Troubleshooting Guide**: Common issues and solutions
* **Security Guide**: Security best practices

Community Support
~~~~~~~~~~~~~~~

* **GitHub Issues**: Report bugs and request features
* **Discussion Forum**: Community discussions and support
* **Slack Channel**: Real-time community chat
* **Stack Overflow**: Technical questions and answers
* **Twitter**: Latest news and updates

Enterprise Support
~~~~~~~~~~~~~~~~

* **Professional Services**: Deployment and optimization assistance
* **Training**: Administrator and developer training
* **Custom Development**: Custom feature development
* **SLA-Based Support**: Guaranteed response times
* **Security Audits**: Regular security assessments