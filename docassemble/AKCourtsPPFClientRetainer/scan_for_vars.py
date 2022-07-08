import re
from docassemble.base.functions import value, define, defined
from docassemble.base.interview_cache import get_interview
from docassemble.base.pandoc import word_to_markdown
from docassemble.base.parse import (InterviewStatus, docx_variable_fix,
                                    get_initial_dict)
from docassemble.base.util import Address, DAFileList, DAFile, Individual, user_info, all_variables, DAEmpty

__all__ = ['get_fields','gather_fields', 'get_multiple_fields','definable','undefinable_fields', 'undefinable_fields_code','pdf_fields_code','set_attribute_to_value']

def set_attribute_to_value(field_list, object_type, attribute, target_value=DAEmpty()):
  """If any item in the list matches object_type, set the specified attribute to DAEmpty() or other value desired"""
  for field in field_list:
    if defined(field) and isinstance(value(field), object_type):
      define(field + '.' + attribute, target_value)

def gather_fields(field_list, exclude=[], skip_undefinable = True, undefinable=None):
  """Trigger the gathering of a list of fields (as strings) in Docassemble. Optionally, skip any fields undefinable in this interview session."""
  if skip_undefinable:
    if undefinable is None:
      undefinable = undefinable_fields(field_list)
    exclude.extend(undefinable)
  for field in field_list:
    if not field in exclude:
      if isinstance(value(field),Individual):
        value(field + '.name.first')
      elif isinstance(value(field),Address):
        value(field + '.address')
      else:
        value(field) # use Docassemble function to require the definition of the field
  
  return True

def get_multiple_fields(file_list, exclude=[]):
  fields = set() 
  if isinstance(file_list,DAFile):
    fields.update(get_fields(file_list))
  else:
    for f in file_list:
      fields.update(get_fields(f))
  return fields

def get_fields(the_file, include_attributes=False):
  """ Get the list of fields needed inside a template file (PDF or Docx Jinja tags)"""
  if isinstance(the_file,DAFileList):
    if the_file[0].mimetype == 'application/pdf':
      return [field[0] for field in the_file[0].get_pdf_fields()]
  else:
    if the_file.mimetype == 'application/pdf':
      return [field[0] for field in the_file.get_pdf_fields()]

  result_file = word_to_markdown(the_file.path(), 'docx')
  if result_file is None:
    # fields = word("Error: no fields could be found in the file")
    return []
  else:
    with open(result_file.name, 'rU', encoding='utf-8') as fp:
      result = fp.read()
      fields = set()
      addresses = r"(\b\S*)(((\.address_block\(\))|(\.address\.on_one_line())))"
      methods = r"(.*)(\..*\(\))"
      # look for variables inside {{ }} tags
      for variable in re.findall(r'{{ *([^\} ]+) *}}', result): # look for all regular fields
        variable = variable.replace("\\","")
        # test if it's a method. if so, scan inside it for variables mentioned
        matches = re.match(methods, variable) 
        if matches:
          fields.add(matches.groups()[0])
        else:           
          fields.add(variable)
        
        # check for implicit reference to address fields in common methods
        matches = re.match(addresses, variable)
        if matches:
          fields.add(matches.groups()[0] + '.address.address')

      # look for all variables inside {% %} tags            
      for variable in re.findall(r'{%[a-z]* for [A-Za-z\_][A-Za-z0-9\_]* in *([^\} ]+) *%}', result): 
        variable = variable.replace("\\","")
        # same test for method as above
        matches = re.match(methods, variable) 
        if matches:
          fields.add(matches.groups()[0])
        else:           
          fields.add(variable)
        del matches
    return [x for x in fields if not "(" in x] # strip out functions/method calls

def undefinable_fields(fields):
  """Given a list of fields names, return a list of all of the fields that can't be defined in the
  current interview."""
  undefined = []
  for field in fields:
    if not definable(field):
      undefined.append(field)
  return undefined

def undefinable_fields_code(fields, undefined=None):
  """Return a list in Docassemble's format with a blank text field to allow the user to enter
    the field even if no existing question in the interview defines it."""
  if undefined is None:
    undefined = undefinable_fields(fields)
  question_code = []
  for field in undefined:
    if "date" in field:
      question_code.append(
        {field: field, 'datatype': 'date'}
      )
    else:
      question_code.append({field: field})
  return question_code      

def pdf_fields_code(fields):
  temp_fields = dict()
  for field in fields:
    temp_fields[field] = value(field)
  return temp_fields

# def definable(the_variable):
#   interview = get_interview(user_info().filename)
#   status = InterviewStatus()
#   try:
#     result = interview.askfor(the_variable, get_initial_dict(), get_initial_dict(), status)
#   except Exception as err:
#     result = err
#   return isinstance(result, dict)

def definable(the_variable):
  """Test if the given variable (as a string) can be defined in the context of the current interview."""
  interview = get_interview(user_info().filename)
  status = InterviewStatus()
  try:
    variables = all_variables(simplify=False)
    result = interview.askfor(the_variable, variables, variables, status)
  except Exception as err:
    result = err
  return isinstance(result, dict)