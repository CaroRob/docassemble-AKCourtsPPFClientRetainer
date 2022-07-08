from docassemble.base.util import defined, Individual

__all__ = ['greet','salute']

def greet(person):
  greeting = ""
  if defined('person.preferred_greeting'):
    greeting = person.preferred_greeting
  else:
    greeting = "Dear"
  greeting += " " + salute(person)
  return greeting

def salute(person):
  greeting = ""
  if defined("person.preferred_salutation"):
    greeting += person.preferred_salutation + " " + person.name.last
  else:
    if defined("person.gender"):
      if person.gender.lower() == 'male':
        greeting += "Mr. " + person.name.last
      elif person.gender.lower() == 'female':
        greeting += "Ms. "  + person.name.last
      else:
        greeting += str(person.name)
    else:
      greeting += str(person.name)
  return greeting