pipeline {
  
    agent any

    parameters {
        booleanParam(name: 'isRelease', defaultValue: false, description: 'Mark as Release')
    }
  
    stages {
       
        stage('Build and Push Docker Image') {
            environment {
                def label_AZ = "kaniko-${UUID.randomUUID().toString()}"
                def label_PaaS = "kaniko-${UUID.randomUUID().toString()}"
                def namespace = "shuttle-san"
                def project = "shuttle-openshift-front-dump"
                def timestamp = sh (returnStdout: true, script: '''
                                                  #!/busybox/sh                                                  
                                                  date +%Y%m%d%H%M
                                                ''').trim()
            }
            parallel{
                stage("Registry: CAN"){
                    steps {                          
                        podTemplate(name: 'kaniko', label: label_PaaS, yaml: readFile('kaniko-paas.yaml')){
                            node(label_PaaS){
                                container (name: 'kaniko', shell: '/busybox/sh') {                      
                                    checkout scm
                                    withCredentials([usernamePassword(credentialsId: 'aplappshuttle-cred', passwordVariable: 'c_PASS', usernameVariable: 'c_USER')]) {
                                        withCredentials([string(credentialsId: 'jenkinstemp', variable: 'JENKINSSECRET')]) {
                                            script{
                                                if (params.isRelease == true) { 
                                                    env.imagetag = "${timestamp}"
                                                } else {  
                                                    env.imagetag = "snapshot"
                                                }
                                            }         
                                            
                                            sh """
                                                sed -i "s|JENKINSKEY|${JENKINSSECRET}|" requirements.txt
                                            """
                                                
                                            sh """
                                                #!/busybox/sh
                                                /kaniko/executor -f ./Dockerfile -c `pwd` --insecure --skip-tls-verify --digest-file /tmp/${BUILD_TAG} --build-arg USERNAME=${c_USER} --build-arg PASSWORD=${c_PASS} --destination=registry.global.ccc.srvb.can.paas.cloudcenter.corp/shuttle-sgt/${project}:${env.imagetag}
                                            """ 
                                        }
                                    }
                                }
                            }   
                        }    
                    }
                }
                stage("Registry: BO"){
                    steps {                          
                        podTemplate(name: 'kaniko', label: label_PaaS, yaml: readFile('kaniko-paas.yaml')){
                            node(label_PaaS){
                                container (name: 'kaniko', shell: '/busybox/sh') {                      
                                    checkout scm
                                    withCredentials([usernamePassword(credentialsId: 'aplappshuttle-cred', passwordVariable: 'c_PASS', usernameVariable: 'c_USER')]) {
                                        withCredentials([string(credentialsId: 'jenkinstemp', variable: 'JENKINSSECRET')]) {
                                            script{
                                                if (params.isRelease == true) { 
                                                    env.imagetag = "${timestamp}"
                                                } else {  
                                                    env.imagetag = "snapshot"
                                                }
                                            }         
                                            
                                            sh """
                                                sed -i "s|JENKINSKEY|${JENKINSSECRET}|" requirements.txt
                                            """
                                                
                                            sh """
                                                #!/busybox/sh
                                                /kaniko/executor -f ./Dockerfile -c `pwd` --insecure --skip-tls-verify --digest-file /tmp/${BUILD_TAG} --build-arg USERNAME=${c_USER} --build-arg PASSWORD=${c_PASS} --destination=registry.global.ccc.srvb.bo.paas.cloudcenter.corp/shuttle-san/${project}:${env.imagetag}
                                            """    
                                        }
                                    }
                                }
                            }   
                        }    
                    }
                }
            }
        }
        stage('Create GitHub Release') {
            when {
                expression { return params.isRelease }
            }
            steps {
                script {
                    def project = "shuttle-openshift-front-dump"
                    def data_release = """
                    { 
                        "tag_name": "${env.imagetag}", 
                        "target_commitish": "develop",
                        "name": "${env.imagetag}", 
                        "body": "Release ${env.imagetag}",
                        "draft": false, "prerelease": false 
                    }
                    """.replaceAll("\\s+", "").trim()

                    echo "Data Release JSON: ${data_release}"
                    withCredentials([string(credentialsId: 'aplappshuttle-gitpush', variable: 'GITHUB_TOKEN')]) {
                        sh """
                            curl -L -k \
                            -H "Accept: application/vnd.github+json" \
                            -H "Content-Type: application/json" \
                            -H "Authorization: Bearer ${GITHUB_TOKEN}" \
                            -d '${data_release}' \
                            https://github.alm.europe.cloudcenter.corp/api/v3/repos/sanes-shuttle/${project}/releases  
                        """
                    }
                }
            }
        } 
        stage ('Launch deploy to DEV') {
            parallel{
                stage("Deploy: BO"){
                    steps {
                        sh """
                        echo 'Build complete, initializing deploy to BO'
                        """
                        build job: """../shuttle-openshift-front-dump-deploy/dev""", parameters: [[$class: 'StringParameterValue', name: 'DOCKER_IMAGE_BO', value: """${imagetag}"""],
                                                                                              [$class: 'StringParameterValue', name: 'region', value: """BO"""]]
    }
}
                stage("Deploy: CAN"){
                    steps {
                        sh """
                        echo 'Build complete, initializing deploy to CAN'
                        """
                        build job: """../shuttle-openshift-front-dump-deploy/dev""", parameters: [[$class: 'StringParameterValue', name: 'DOCKER_IMAGE_CAN', value: """${imagetag}"""],
                                                                                              [$class: 'StringParameterValue', name: 'region', value: """CAN"""]]
                    }
                }
            }
        }
    }
}
