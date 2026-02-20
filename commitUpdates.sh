#!/bin/bash

source activate urubu
make 

echo -e "build"
cp -R _build/* ../akpetty.github.io

# Copy .gitignore to destination repo
if [ -f .gitignore ]; then
    cp .gitignore ../akpetty.github.io/
fi

echo -e "commit to Git"
cd ../akpetty.github.io

echo -e "pull any missing commits"
git pull

git add --all
git commit -m "update"
echo -e "Pushing to akpetty.github.io"
git push origin master

echo -e "Done"

