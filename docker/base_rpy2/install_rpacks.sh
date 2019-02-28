
echo "broom\n\
      DBI\n\
      dbplyr\n\
      dplyr\n\
      hexbin\n\
      ggplot2\n\
      lme4\n\
      RSQLite\n\
      tidyr" > rpacks.txt && \
R -e 'install.packages(sub("(.+)\\\\n","\\1", scan("rpacks.txt", "character")), repos="'"${CRAN_MIRROR}"'")' && \
rm rpacks.txt
