jq -c '.version = .version +1' config.json > tmp.json && mv tmp.json config.json

git commit -a -m "automated"
git push
