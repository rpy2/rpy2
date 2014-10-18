import jinja2
from IPython.display import HTML

css = """
<style>
table.rpy2 {
  border: solid 1px rgb(180, 180, 180);
  border-radius: 4px;
  -moz-border-radius: 4px;
}
table.rpy2 th {
  background-color: rgb(215, 215, 215);
  border-top: none;
}
table.rpy2 td {
  text-align: right;
  font-family: monospace;
}
table.rpy2 td:first-child {
  border-left: none;
}
</style>
"""

template_list = jinja2.Template("""
<p><emph>{{ clsname }}</emph> with {{ rlist | length }} elements:</p>
<ul class="rpy2">
{%- for elt_i in range(display_neltmax) %}
      <li><b>{{ rlist.names[elt_i] }} :</b> {{ rlist[elt_i] }}</li>
{%- endfor %}
{%- if display_neltmax < (rlist | length) %}
      <li>...</li>  
{%- endif %}
</ul>
""")

template_vector = jinja2.Template(css+"""
<table class="rpy2">
<thead>
</thead>
<tbody>
<tr>
  {%- for elt_i in range(display_ncolmax - 2) %}
  <td>{{ vector[elt_i]}}</td>
  {%- endfor %}
  {%- if display_ncolmax < (vector | length) %}
  <td>...</td>  
  {%- endif %}
  {%- for elt_i in elt_i_tail %}
      <td>{{ vector[elt_i] }}</td>
  {%- endfor %}
</tr>
</tbody>
</table>
""")

template_dataframe = jinja2.Template(css+"""
<emph>{{ clsname }}</emph> with {{ dataf | length }} columns:
<table class="rpy2">
  <thead>
    <tr>
{%- for col_i in range(display_ncolmax - 2) %}
      <th>{{ dataf.names[col_i] }}</th>
{%- endfor %}
{%- if display_ncolmax < dataf.ncol %}
      <th>...</th>  
{%- endif %}
{%- for col_i in col_i_tail %}
      <th>{{ dataf.names[col_i] }}</th>
{%- endfor %}
    </tr>
  </thead>
  <tbody>
{%- for row_i in range(display_nrowmax - 3) %}
    <tr>
  {%- for col_i in range(display_ncolmax - 2) %}
      <td>{{ dataf[col_i][row_i] }}</td>
  {%- endfor %}
  {%- if display_ncolmax < dataf.ncol %}
       <td>...</td>  
  {%- endif %}
  {%- for col_i in col_i_tail %}
      <td>{{ dataf[col_i][row_i] }}</td>
  {%- endfor %}
    </tr>
{%- endfor %}

{%- if dataf.nrow > display_nrowmax %}
    <tr>
  {%- for col_i in range(display_ncolmax - 2) %}
      <td>...</td>
  {%- endfor %}
  {%- if display_ncolmax < dataf.ncol %}
       <td>...</td>  
  {%- endif %}
  {%- for col_i in range(2) %}
      <td>...</td>
  {%- endfor %}
    </tr>
{%- endif %}

{%- for row_i in row_i_tail %}
    <tr>
  {%- for col_i in range(display_ncolmax - 2) %}
      <td>{{ dataf[col_i][row_i] }}</td>
  {%- endfor %}
  {%- if display_ncolmax < dataf.ncol %}
       <td>...</td>  
  {%- endif %}
  {%- for col_i in col_i_tail %}
      <td>{{ dataf[col_i][row_i] }}</td>
  {%- endfor %}
    </tr>
{%- endfor %}
  </tbody>
</table>
""")

template_ridentifiedobject = jinja2.Template("""
<ul style="list-style-type: none;">
<li>{{ clsname }} object</li>
<li>Origin in R: {{ origin }}</li>
<li>Class(es) in R:
  <ul>
  {%- for rclsname in obj.rclass %}
    <li>{{ rclsname }}</li>
  {%- endfor %}
  </ul>
</li>
</ul>
""")

template_rs4 = jinja2.Template("""
<ul style="list-style-type: none;">
<li>{{ clsname }} object</li>
<li>Origin in R: {{ origin }}</li>
<li>Class(es) in R:
  <ul>
  {%- for rclsname in obj.rclass %}
    <li>{{ rclsname }}</li>
  {%- endfor %}
  </ul>
</li>
<li> Attributes:
  <ul>
  {%- for sln in obj.slotnames() %}
    <li>{{ sln }}</li>
  {%- endfor %}
  </ul>
</li>
</ul>
""")


from rpy2.robjects import (vectors, 
                           RObject, 
                           SignatureTranslatedFunction,
                           RS4)

def html_vector(vector):
    html = template_vector.render({
        'clsname': type(vector).__name__,
        'vector': vector,
        'display_ncolmax': min(10, len(vector)),
        'elt_i_tail': range(max(0, len(vector)-2), len(vector))})
    return html
def html_rlist(rlist):
    html = template_list.render({
        'clsname': type(rlist).__name__,
        'rlist': rlist,
        'display_neltmax': min(10, len(rlist))})
    return html

def html_rdataframe(dataf):
    html = template_dataframe.render(
        {'dataf': dataf,
         'clsname': type(dataf).__name__,
         'display_nrowmax': min(10, dataf.nrow),
         'display_ncolmax': min(6, dataf.ncol),
         'col_i_tail': range(max(0, dataf.ncol-2), dataf.ncol),
         'row_i_tail': range(max(0, dataf.nrow-2), dataf.nrow)
     })
    return html


# FIXME: wherefrom() is taken from the rpy2 documentation
# May be it should become part of the rpy2 API
from rpy2 import rinterface
def wherefrom(name, startenv=rinterface.globalenv):
    """ when calling 'get', where the R object is coming from. """
    env = startenv
    obj = None
    retry = True
    while retry:
        try:
            obj = env[name]
            retry = False
        except LookupError:
            env = env.enclos()
            if env.rsame(rinterface.emptyenv):
                retry = False
            else:
                retry = True
    return env

def _dict_ridentifiedobject(obj):
    if hasattr(obj, '__rname__') and obj.__rname__ is not None:
        env = wherefrom(obj.__rname__)
        try:
            origin = env.do_slot('name')[0]
        except LookupError:
            origin = 'package:base ?'
    else:
        origin = '???'
    d = {'clsname': type(obj).__name__,
         'origin': origin,
         'obj': obj}
    return d

def html_ridentifiedobject(obj):
    d = _dict_ridentifiedobject(obj)
    html = template_ridentifiedobject.render(d)
    return html

def html_rs4(obj):
    d = _dict_ridentifiedobject(obj)
    html = template_rs4.render(d)
    return html


def init_printing():
    ip = get_ipython()
    html_f = ip.display_formatter.formatters['text/html']
    html_f.for_type(vectors.Vector, html_vector)
    html_f.for_type(vectors.ListVector, html_rlist)
    html_f.for_type(vectors.DataFrame, html_rdataframe)
    html_f.for_type(RObject, html_ridentifiedobject)
    html_f.for_type(RS4, html_rs4)
    html_f.for_type(SignatureTranslatedFunction, html_ridentifiedobject)
    from IPython.display import HTML
    HTML(css)

