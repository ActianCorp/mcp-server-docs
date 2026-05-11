//------------------------------------------------------------------------------
// Jenkinsfile for ActianCorp/mcp-server-docs
//------------------------------------------------------------------------------

//----- functions, methods -----------------------------------------------------
//post notifications
def sendMessages() {
    echo "--> sendMessages()"
    script {
        if ( DEVOPS_BUILD.toBoolean() == false ) {
            emailext(
                body: '${DEFAULT_CONTENT}',
                mimeType: 'text/html',
                replyTo: '${DEFAULT_REPLYTO}',
                subject: '${DEFAULT_SUBJECT}',
                to: "${EMAIL_RECIPIENTS}",
                recipientProviders: [culprits(), requestor()]
            )
        } else {
            echo "--- DevOps build, SKIP sendMessages() ---"
        }
    }
}

pipeline {
    agent { label 'default-agent' }

    // triggers{
    //     pollSCM('H/5 * * * *')
    // }

    options {
        buildDiscarder(logRotator(numToKeepStr: '5'))
    }

    environment {
        DOC_VERSION=1.0
        DOCNAME="${JOB_NAME}"
        DOC_NAME_VERSION="mcp-server-${DOC_VERSION}.doc"

        EMAIL_RECIPIENTS='jim.mccaskey@hcl-software.com, ' +
            'bipinkumar.pandey@hcl-software.com, cody.kern@hcl-software.com, mike.zayour@hcl-software.com'
    }

    stages {
        stage('Cleanup Previous Build and Configure Build') {
            steps {
                sh "rm *.log 2>/dev/null || true"
                script {
                    if ( !env.BRANCH_NAME) { // non-multibranch pipeline does not provide BRANCH_NAME, need to set manually
                        env.BRANCH_NAME = scm.branches[0].name
                    }

                    if ( BRANCH_NAME =~ "feature/DEVOPS-*" || BRANCH_NAME =~ "bugfix/DEVOPS-*") {
                        env.DEVOPS_BUILD = true
                    } else {
                        env.DEVOPS_BUILD = false
                    }
                    env.REPO_COMMIT_URL_ANCHOR = "[${GIT_COMMIT[0..6]}](https://github.com/ActianCorp/mcp-server-docs/commit/${GIT_COMMIT})"
                    currentBuild.description = "**Commit**: ${REPO_COMMIT_URL_ANCHOR}"

                    echo "JOB_BASE_NAME:             [" + JOB_BASE_NAME + "]"
                    echo "JOB_NAME:                  [" + JOB_NAME + "]"
                    echo "BUILD_NUMBER:              [" + BUILD_NUMBER + "]"
                    echo "BRANCH_NAME:              [" + BRANCH_NAME + "]"
                    echo "DEVOPS_BUILD:             [" + DEVOPS_BUILD + "]"
                    echo "GIT_COMMIT:               [" + GIT_COMMIT + "]"
                    echo "REPO_COMMIT_URL_ANCHOR:   [" + REPO_COMMIT_URL_ANCHOR + "]"
                }
                sh "set | sort > _${JOB_BASE_NAME}_init_env-${BUILD_NUMBER}.log"
            }
            post {
                always {
                    archiveArtifacts allowEmptyArchive: true, artifacts: '*.log'
                }
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    python3 --version
                    python3 -m pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Build MkDocs site') {
            steps {
                sh 'mkdocs build --clean'
            }
        }

        stage('Package output for deploy') {
            steps {
                sh 'zip -r output.zip site'
                archiveArtifacts artifacts: 'output.zip', onlyIfSuccessful: true
                stash includes: 'output.zip', name: 'output.zip', useDefaultExcludes: false
            }
        }

        stage('Publish to aws-docserver') {
            when {
                branch "release/mcp-server-${DOC_VERSION}.doc"
            }
            agent { label 'aws-docserver' }
            // We don't need the source checked out to the web server
            options { skipDefaultCheckout true }
            steps {
                unstash 'output.zip'
                fileOperations([fileUnZipOperation(filePath: 'output.zip', targetLocation: '.')])
                bat "move D:\\Sites\\mcp-server D:\\backups\\mcp-server-${DOC_VERSION}-${BUILD_NUMBER}.backup"
                bat "move ${WORKSPACE}\\site D:\\Sites\\mcp-server"
            }
        }
    }

    post
    {
        always {
            echo '----- post/always -----'
            logParser failBuildOnError: true, parsingRulesPath: '/var/lib/jenkins/documentation_log_parsing.txt',
                projectRulePath: '/var/lib/jenkins/documentation_log_parsing.txt', useProjectRule: false
        }
        success {
            echo '----- post/success -----'
            cleanWs()
        }
        unsuccessful {
            // unstable, fail, or abort
            echo '----- post/unsuccessful -----'
            sendMessages()
        }
        fixed{
            // unstable or fail -> success
            echo '----- post/fixed -----'
            sendMessages()
        }
    }
}
