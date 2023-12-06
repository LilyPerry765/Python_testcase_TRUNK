pipeline {
    agent {
        docker {
            image 'ubuntu'
            args '-u root:root'
        }

    }

    environment {
        SSH_deploy = credentials('9ff10bb8-8b88-4165-8524-0cbc6b825a5d')
    }
    stages {

        stage('deploy-115') {
        when {
                branch 'develop'
            }
            steps {
                sh '''#!/bin/bash
                    eval $(ssh-agent -s)
                    cat $SSH_deploy | tr -d '\r' | ssh-add -
                    scp -r -o StrictHostKeyChecking=no root@172.22.132.115:/usr/local/src/rspsrv/rspsrv/settings/local.env rspsrv/settings/local.env
                    ssh -t -o StrictHostKeyChecking=no root@172.22.132.115 ' mv /usr/local/src/rspsrv /usr/local/src/rspsrv.back'
                    scp -r -o StrictHostKeyChecking=no . root@172.22.132.115:/usr/local/src/rspsrv
                    ssh -t -o StrictHostKeyChecking=no root@172.22.132.115 'systemctl restart api ari'

                 '''
            }
        }
        
    }
}
