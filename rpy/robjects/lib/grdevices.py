import rpy2.robjects.methods
import rpy2.robjects as robjects
import rpy2.robjects.conversion as conversion

#getmethod = robjects.baseenv.get("getMethod")

rimport = robjects.baseenv.get('library')
rimport('grDevices')

grdevices_env = robjects.baseenv['as.environment']('package:grDevices')


png = grdevices_env['png']
pdf = grdevices_env['pdf']
svg = grdevices_env['svg']
x11 = grdevices_env['x11']

postscript = grdevices_env['postscript']

dev_off = grdevices_env['dev.off']
dev_copy = grdevices_env['dev.copy']
dev_cur = grdevices_env['dev.cur']
dev_interactive = grdevices_env['dev.interactive']


