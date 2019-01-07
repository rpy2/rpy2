#!/usr/bin/env r

if (is.null(argv) | length(argv)<1) {
  cat("Usage: installr.r pkg1 [pkg2 pkg3 ...]\n")
  q()
}

repos <- "https://cran.rstudio.com" 

install.packages(argv, repos=repos)
