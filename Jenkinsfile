pipeline {
    agent any

    environment {
        // Map the secret text credential to the environment variable gh expects
        GITHUB_TOKEN = credentials('GITHUB_TOKEN')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Verify GitHub CLI') {
            steps {
                // Confirm the installation works
                sh 'gh --version'
            }
        }

        stage('Test') {
            steps {
                sh 'PYTHONPATH=$(pwd) python3 -m unittest discover tests'
            }
        }

        stage('Build & GitHub Release (Both Packages)') {
            steps {
                // This runs `make release` which now builds both
                // the official and engineering .deb packages and uploads them
                sh 'make release'
            }
        }
    }

    post {
        success {
            archiveArtifacts artifacts: '*.deb', allowEmptyArchive: false
            echo 'Debian package successfully built, archived in Jenkins, and released to GitHub!'
        }
        failure {
            echo 'Pipeline failed. Check the logs for more information.'
        }
    }
}
