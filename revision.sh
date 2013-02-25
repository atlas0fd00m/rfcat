
hg parent >/dev/null 2>&1
if [ $? -eq 0 ]; then
    hg parent --template '{rev}' | tee .revision
else
    [ -e .revision ] && cat .revision || echo '65535'
fi

