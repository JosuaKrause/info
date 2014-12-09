#export JAVA_HOME=/usr
cd ../JKanvas/
mvn -DaltDeploymentRepository=repo::default::file:../mvn-repo/releases clean deploy
