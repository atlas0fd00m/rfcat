
git rev-list HEAD >/dev/null 2>&1
if [ $? -eq 0 ]; then
    git rev-list HEAD --count | tee .revision
else
    [ -e .revision ] && cat .revision || echo '65535'
fi

