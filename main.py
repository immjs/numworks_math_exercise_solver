digits = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
variable_names = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

def group(callback, arr):
  groups = {}
  for i in arr:
    groups.setdefault(callback(i), []).append(i)
  return groups

def isfloat(num):
  try:
    float(num)
    return True
  except ValueError:
    return False

def properly_format(str):
  str = ''.join(str.split())
  new_str = []
  paren_min_nest = float('inf')
  paren_nest_level = 0
  for i in range(0, len(str)):
    new_str.append(str[i])
    if i != len(str) - 1 and str[i+1] in ['('] + variable_names and str[i] in [')'] + digits + variable_names:
      new_str.append('*')
  str = ''.join(new_str)
  for i in range(0, len(str)):
    if str[i] == '(':
      paren_nest_level += 1
    elif str[i] == ')':
      paren_nest_level -= 1
    elif paren_nest_level < paren_min_nest:
      paren_min_nest = paren_nest_level
  return str[paren_min_nest:(len(str) - paren_min_nest)]

def look_for(str, operator):
  paren_nest_level = 0;
  inner = []
  latest_substr = 0
  for i in range(len(str)):
    if str[i] == '(':
      paren_nest_level += 1
    elif str[i] == ')':
      paren_nest_level -= 1
    elif str[i] in operator and paren_nest_level == 0:
      inner.append(str[latest_substr:i])
      latest_substr = i + 1
  inner.append(str[latest_substr:len(str)])
  return inner

class Expr:
  @classmethod
  def from_expr(cls, expr):
    if isinstance(expr, cls):
      return cls(*expr.children)
    else:
      return cls(expr)

  @staticmethod
  def from_string(str):
    str = properly_format(str)
    pluses = look_for(str, {
      '+': lambda x: x,
      '-': lambda x: x.opposite(),
    })
    if len(pluses) != 1:
      return Sum(*map(Expr.from_string, pluses))
    times = look_for(str, {
      '*': lambda x: x,
      '/': lambda x: x.inverse(),
    })
    if len(times) != 1:
      return Product(*map(Expr.from_string, times))
    return Unit(str)

  def __init__(self, *exprs):
    self.children = list(exprs)

  def __str__(self):
    def with_paren(child):
      if child.priority < self.priority:
        return "({})".format(child.__str__())
      else:
        return child.__str__()
    return self.sign.join(
      map(
        with_paren,
        self.children,
      )
    )

  @classmethod
  def flatten(cls, *exprs):
    res = []
    for i in exprs:
      if i.priority < cls.priority:
        raise TypeError('Cannot flatten expression with lower priority into product')
      if isinstance(i, cls):
        res += cls.flatten(*i.children)
      else:
        res.append(i)
    return res
    
  def may_vary(self):
    return any(map(lambda x: x.may_vary(), self.children))

class Sum(Expr):
  priority=0
  sign='+'
  identity=0
  def __init__(self, *exprs):
    super().__init__(*exprs)

  def exec(self):
    result = Sum()
    for child in self.children:
      childcopy = child.exec()
      result.children.append(childcopy)
    letterpos = []
    def sortfn(x):
      non_variable_factors = x.filter(lambda x: not x.may_vary())
      print(non_variable_factors)
      # if 
    # result.children = result.children.sorted()
    return result

class Product(Expr):
  priority=1
  sign='*'
  identity=1
  def __init__(self, *exprs):
    super().__init__(*exprs)
    
  @staticmethod
  def factorize_from_exprs(*exprs):
    sums = list(map(Sum.from_expr, exprs))
    terms = Sum()
    for a in sums[0].children:
      for b in sums[1].children:
        terms.children.append(Product(a, b))
    return terms

  def factorize(self):
    if len(self.children) > 2:
      return Product.factorize_from_exprs(*self.children[:-2], Product.factorize_from_exprs(*self.children[-2:]))
    return Product.factorize_from_exprs(*self.children)

  def exec(self):
    if any(map(lambda x: isinstance(x, Sum), self.children)):
      raise TypeError('Trying to exec yet some additions remain')
      
    flattened = Product.flatten(*self.children)

    numbers = 1.0
    variables = {}

    for child in flattened:
      if isinstance(child, Exp):
        variables.setdefault(child.base.unit, 0)
        variables[child.base.unit] += child.exp.unit
      elif child.is_variable:
        variables.setdefault(child.unit, 0)
        variables[child.unit] += 1
      else:
        numbers *= child.unit
    result = Product(*([Unit(numbers)] if numbers != 0 else []))
    for variable in variables:
      insert_me = Unit(variable)
      if variables[variable] != 1:
        insert_me = Exp(
          Unit(variable),
          Unit(variables[variable]),
        )
      result.children.append(insert_me)
    return result
        

class Exp(Expr):
  priority=3
  sign='^'
  identity=1
  def __init__(self, base, exp):
    if not exp:
      exp = self.identity
    super().__init__(base, exp)
    self.base = base
    self.exp = exp

class Unit:
  priority=5
  def __init__(self, unit):
    if isfloat(unit):
      self.unit=float(unit)
      self.is_variable=False
    else:
      self.unit=unit
      self.is_variable=True
    self.base=self
  def __str__(self):
    return str(self.unit)
  def may_vary(self):
    return self.is_variable

expr = Expr.from_string('(x+1)(7+2x)')
print(expr)
print(expr.factorize())
print(expr.factorize().exec())