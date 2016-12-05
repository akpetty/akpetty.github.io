#!/bin/bash

source activate urubu
make 

echo -e "build"
cp -R _build ../akpetty.github.io

echo -e "commit to Git"
cd ../akpetty.github.io

git add --all
git commit -m "update"
echo -e "Pushing to akpetty.github.io"
git push origin master

echo -e "Done"


