/*
 ***** BEGIN LICENSE BLOCK *****
 * Version: MPL 1.1/GPL 2.0/LGPL 2.1
 *
 * The contents of this file are subject to the Mozilla Public License Version
 * 1.1 (the "License"); you may not use this file except in compliance with
 * the License. You may obtain a copy of the License at
 * http://www.mozilla.org/MPL/
 *
 * Software distributed under the License is distributed on an "AS IS" basis,
 * WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
 * for the specific language governing rights and limitations under the
 * License.
 * 
 * Copyright (C) 2008-2013 Laurent Gautier
 *
 * Alternatively, the contents of this file may be used under the terms of
 * either the GNU General Public License Version 2 or later (the "GPL"), or
 * the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
 * in which case the provisions of the GPL or the LGPL are applicable instead
 * of those above. If you wish to allow use of your version of this file only
 * under the terms of either the GPL or the LGPL, and not to allow others to
 * use your version of this file under the terms of the MPL, indicate your
 * decision by deleting the provisions above and replace them with the notice
 * and other provisions required by the GPL or the LGPL. If you do not delete
 * the provisions above, a recipient may use your version of this file under
 * the terms of any one of the MPL, the GPL or the LGPL.
 *
 * ***** END LICENSE BLOCK ***** */

#include <Rdefines.h>

SEXP rpy_serialize(SEXP object, SEXP rho)
{
  SEXP c_R, call_R, res, fun_R;

  PROTECT(fun_R = PyRinterface_FindFun(install("serialize"), rho));
  if(!isEnvironment(rho)) error("'rho' should be an environment");
  /* obscure incatation to summon R */
  PROTECT(c_R = call_R = allocList(3));
  SET_TYPEOF(c_R, LANGSXP);
  SETCAR(c_R, fun_R);
  c_R = CDR(c_R);

  /* first argument is the SEXP object to serialize */
  SETCAR(c_R, object);
  c_R = CDR(c_R);

  /* second argument is NULL */
  SETCAR(c_R, R_NilValue);
  c_R = CDR(c_R);
  PROTECT(res = eval(call_R, rho));
  UNPROTECT(3);
  return res;
}

SEXP rpy_unserialize(SEXP connection, SEXP rho)
{
  SEXP c_R, call_R, res, fun_R;
  PROTECT(fun_R = PyRinterface_FindFun(install("unserialize"), rho));
  if(!isEnvironment(rho)) error("'rho' should be an environment");
  /* obscure incatation to summon R */
  PROTECT(c_R = call_R = allocList(2));
  SET_TYPEOF(c_R, LANGSXP);
  SETCAR(c_R, fun_R);
  c_R = CDR(c_R);

  /* first argument is a RAWSXP representation of the object to unserialize */
  SETCAR(c_R, connection);
  c_R = CDR(c_R);
  
  PROTECT(res = eval(call_R, rho));
  UNPROTECT(2);
  return res;
}

SEXP rpy_list_attr(SEXP sexp)
{
  SEXP attrs, res;
  int nvalues, attr_i;

  attrs = ATTRIB(sexp);
  nvalues = GET_LENGTH(attrs);
  PROTECT(res = allocVector(STRSXP, nvalues));

  attr_i = 0;
  while (attrs != R_NilValue) {
    if (TAG(attrs) == R_NilValue)
      SET_STRING_ELT(res, attr_i, R_BlankString);
    else
      SET_STRING_ELT(res, attr_i, PRINTNAME(TAG(attrs)));
    attrs = CDR(attrs);
    attr_i++;
  }
  UNPROTECT(1);
  return res;
}

SEXP rpy_remove(SEXP symbol, SEXP env, SEXP rho)
{
  SEXP c_R, call_R, res;

  static SEXP fun_R = NULL;
  if (fun_R == NULL) {
    PROTECT(fun_R = PyRinterface_FindFun(install("rm"), rho));
    /* FIXME: or use the rpy2 object tracking layer ?*/
    R_PreserveObject(fun_R);
    UNPROTECT(1);
  }
  
  if(!isEnvironment(rho)) error("'rho' should be an environment");
  /* incantation to summon R */
  PROTECT(c_R = call_R = allocList(2+1));
  SET_TYPEOF(c_R, LANGSXP);
  SETCAR(c_R, fun_R);
  c_R = CDR(c_R);

  /* first argument is the name of the variable to be removed */
  SETCAR(c_R, symbol);
  //SET_TAG(c_R, install("list"));
  c_R = CDR(c_R);

  /* second argument is the environment in which the variable 
     should be removed  */
  SETCAR(c_R, env);
  SET_TAG(c_R, install("envir"));
  c_R = CDR(c_R);

  int error = 0;
  PROTECT(res = R_tryEval(call_R, rho, &error));

  UNPROTECT(2);
  return res;
}

SEXP
rpy_lang2str(SEXP sexp, SEXPTYPE t) {
  SEXP symbol = CAR(sexp);
  static struct{
    SEXP if_sym;
    SEXP while_sym;
    SEXP for_sym; 
    SEXP eq_sym;
    SEXP gets_sym;
    SEXP lpar_sym; 
    SEXP lbrace_sym;
    SEXP call_sym;
  } s_str = {0, 0, 0, 0, 0, 0, 0, 0};
  if(!s_str.if_sym) {
    s_str.if_sym = install("if");
    s_str.while_sym = install("while");
    s_str.for_sym = install("for");
    s_str.eq_sym = install("=");
    s_str.gets_sym = install("<-");
    s_str.lpar_sym = install("(");
    s_str.lbrace_sym = install("{");
    s_str.call_sym = install("call");
  }
  if(Rf_isSymbol(symbol)) {
    if(symbol == s_str.if_sym || symbol == s_str.for_sym || symbol == s_str.while_sym ||
       symbol == s_str.lpar_sym || symbol == s_str.lbrace_sym ||
       symbol == s_str.eq_sym || symbol == s_str.gets_sym)
      return PRINTNAME(symbol);
  }
  return PRINTNAME(s_str.call_sym);
	
}
