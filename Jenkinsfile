// CI/CD pipeline for EdgeGuard.
// Runs on every commit (SCM polling): unit tests in Docker -> build image ->
// smoke test -> optional push to Docker Hub -> deploy to the local test server.
pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    // Jenkins checks GitHub every ~2 minutes and starts a build for each new commit.
    triggers {
        pollSCM('H/2 * * * *')
    }

    parameters {
        booleanParam(name: 'PUSH_TO_DOCKERHUB', defaultValue: false,
                     description: 'Push the image to Docker Hub (needs credentials with id "dockerhub")')
        booleanParam(name: 'DEPLOY', defaultValue: true,
                     description: 'Deploy the new image to the test server (http://localhost:8501)')
    }

    environment {
        IMAGE = 'edgeguard'
        TAG = "${env.BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'git log -1 --pretty=format:"%h %an: %s"'
            }
        }

        stage('Unit tests') {
            steps {
                sh 'docker build --target test -t ${IMAGE}:test-${TAG} .'
                sh '''
                    docker rm -f edgeguard-test-${TAG} >/dev/null 2>&1 || true
                    docker run --name edgeguard-test-${TAG} ${IMAGE}:test-${TAG}
                '''
            }
            post {
                always {
                    sh '''
                        mkdir -p reports
                        docker cp edgeguard-test-${TAG}:/reports/junit.xml reports/junit.xml || true
                        docker rm -f edgeguard-test-${TAG} >/dev/null 2>&1 || true
                        docker rmi ${IMAGE}:test-${TAG} >/dev/null 2>&1 || true
                    '''
                    junit allowEmptyResults: true, testResults: 'reports/junit.xml'
                }
            }
        }

        stage('Build Docker image') {
            steps {
                sh 'docker build --target runtime -t ${IMAGE}:${TAG} -t ${IMAGE}:latest .'
                sh 'docker image ls ${IMAGE}'
            }
        }

        stage('Smoke test') {
            steps {
                // The built image must run the scientific module end to end.
                sh 'docker run --rm ${IMAGE}:${TAG} edgeguard benchmark -n 300'
            }
        }

        stage('Push to Docker Hub') {
            when { expression { params.PUSH_TO_DOCKERHUB } }
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub',
                                                  usernameVariable: 'DH_USER',
                                                  passwordVariable: 'DH_PASS')]) {
                    sh '''
                        echo "$DH_PASS" | docker login -u "$DH_USER" --password-stdin
                        docker tag ${IMAGE}:${TAG} "$DH_USER/${IMAGE}:${TAG}"
                        docker tag ${IMAGE}:${TAG} "$DH_USER/${IMAGE}:latest"
                        docker push "$DH_USER/${IMAGE}:${TAG}"
                        docker push "$DH_USER/${IMAGE}:latest"
                        docker logout
                    '''
                }
            }
        }

        stage('Deploy to test server') {
            when { expression { params.DEPLOY } }
            steps {
                sh '''
                    docker rm -f edgeguard-staging >/dev/null 2>&1 || true
                    docker run -d --name edgeguard-staging --restart unless-stopped \
                        -p 8501:8501 ${IMAGE}:${TAG}
                    echo "Waiting for the container to become healthy..."
                    for i in $(seq 1 30); do
                        STATUS=$(docker inspect -f '{{.State.Health.Status}}' edgeguard-staging)
                        echo "  health: $STATUS"
                        if [ "$STATUS" = "healthy" ]; then
                            echo "Deployed: http://localhost:8501"
                            exit 0
                        fi
                        sleep 3
                    done
                    docker logs edgeguard-staging
                    exit 1
                '''
            }
        }
    }

    post {
        success { echo "Build ${env.BUILD_NUMBER} passed: image ${env.IMAGE}:${env.TAG}" }
        failure { echo 'Pipeline failed — check the stage logs above.' }
        always  { sh 'docker image prune -f >/dev/null 2>&1 || true' }
    }
}
