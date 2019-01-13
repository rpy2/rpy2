args <- commandArgs(trailingOnly = TRUE)

repos <- "https://cran.rstudio.com" 

install.packages(args, repos = repos)
