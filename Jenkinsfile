pipeline {
    agent none

    options {
        timestamps()
    }

    stages {
        stage('Backend') {
            agent {
                docker { image 'python:3.12-slim' }
            }
            environment {
                DATABASE_ENGINE = 'sqlite'
            }
            steps {
                checkout scm
                dir('backend') {
                    sh '''
                        pip install --no-cache-dir -r requirements-dev.txt
                        ruff format --check .
                        ruff check .
                        python manage.py test
                    '''
                }
            }
        }

        stage('Frontend') {
            agent {
                docker { image 'node:22-alpine' }
            }
            steps {
                checkout scm
                dir('frontend') {
                    sh '''
                        npm ci
                        npm run lint
                        npm run test -- --run
                        npm run build
                    '''
                }
            }
        }
    }
}
