pipeline {
    agent none

    options {
        timestamps()
    }

    stages {
        stage('Backend') {
            agent {
                docker {
                    image 'python:3.12-slim'
                }
            }

            environment {
                DATABASE_ENGINE = 'sqlite'
                DJANGO_SECRET_KEY = 'chave-de-teste-ci-nao-usar-em-producao'
            }

            steps {
                checkout scm

                dir('backend') {
                    sh '''
                        python -m venv .venv

                        .venv/bin/python -m pip install --upgrade pip
                        .venv/bin/python -m pip install --no-cache-dir -r requirements-dev.txt

                        .venv/bin/ruff format --check .
                        .venv/bin/ruff check .
                        .venv/bin/python manage.py test
                    '''
                }
            }
        }

        stage('Frontend') {
            agent {
                docker {
                    image 'node:22-alpine'
                }
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
