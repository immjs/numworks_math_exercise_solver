digits = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
variable_names = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

#############
#  METHODS  #
#############

def flatten_lists_of_lists(t):
  return [item for sublist in t for item in sublist]

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
  str = ''.join(str.split(' '))
  new_str = []
  paren_min_nest = float('inf')
  paren_nest_level = 0

  for i in range(0, len(str)):
    if (i == 0 or str[i - 1] == '(') and str[i] == '-':
      new_str.append('0')

    if not ((i == 0 or str[i - 1] == '(') and str[i] == '+'):
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

def look_for(str, operators):
  paren_nest_level = 0;
  inner = {}
  latest_substr = 0
  latest_op = operators[0]
  for i in range(len(str)):
    if str[i] == '(':
      paren_nest_level += 1
    elif str[i] == ')':
      paren_nest_level -= 1
    elif str[i] in operators and paren_nest_level == 0:
      inner.setdefault(latest_op, []).append(str[latest_substr:i])
      latest_op = str[i]
      latest_substr = i + 1
  inner.setdefault(latest_op, []).append(str[latest_substr:len(str)])
  print(inner)
  return inner

#############
#  E X P R  #
#############

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
    print(str)
    pluses = look_for(str, ['+', '-'])
    if len(flatten_lists_of_lists(pluses.values())) != 1:
      print(list(map(Opposite, map(Expr.from_string, pluses['-']))))
      return Sum(*(
        list(map(
          Expr.from_string,
          pluses.setdefault('+', []),
        ))
        + list(map(
          Opposite,
          map(
            Expr.from_string,
            pluses.setdefault('-', []),
          )
        ))
      ))
    times = look_for(str, ['*', '/'])
    if len(flatten_lists_of_lists(times.values())) != 1:
      return Product(*(
        list(map(
          Expr.from_string,
          times.setdefault('*', []),
        ))
        + list(map(
          Inverse,
          map(
            Expr.from_string,
            times.setdefault('/', []),
          )
        ))
      ))
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

#############
#    SUM    #
#############

class Sum(Expr):
  priority=1
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
      variable_factors = map(
        lambda x: Exp.from_expr(x),
        filter(
          lambda x: x.may_vary(),
          Product.from_expr(x).children,
        ),
      )
      print(list(variable_factors))
      return 1
      # if 
    result.children = sorted(result.children, key=sortfn)
    return result

#############
#  PRODUCT  #
#############

class Product(Expr):
  priority=2
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
      return Product.factorize_from_exprs(*(self.children[:-2] + [Product.factorize_from_exprs(*(self.children[-2:]))]))
    return Product.factorize_from_exprs(*self.children)

  def exec(self):
    if any(map(lambda x: isinstance(x, Sum), self.children)):
      raise TypeError('Trying to exec yet some additions remain')
      
    flattened = Product.flatten(*self.children)

    removed_identity = list(filter(lambda x: x != self.identity, flattened))

    numbers = 1.0
    variables = {}

    for child in removed_identity:
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

#############
#    EXP    #
#############

class Exp(Expr):
  priority=3
  sign='^'
  identity=1
  @classmethod
  def from_expr(cls, expr):
    if isinstance(expr, cls):
      return cls(*expr.children)
    else:
      return cls(expr, cls.identity)
  def __init__(self, base, exp):
    if not exp:
      exp = self.identity
    super().__init__(base, exp)
    self.base = base
    self.exp = exp

#############
#  U N I T  #
#############

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

#############
#  OPPOSIT  #
#############

class Opposite(Product):
  priority=4
  sign='-'
  def __init__(self, expr):
    super().__init__(expr, Unit(-1.0))
    self.expr = expr
  def __str__(self):
    print('str called')
    return '-({})'.format(self.expr)

#############
#  INVERSE  #
#############

class Inverse(Product):
  priority=4
  sign='/'
  def __init__(self, expr):
    super().__init__(expr, Unit(-1.0))
    print('initialised')
    self.expr = expr
  def exec(self):
    return Exp(self.expr, Unit(-1.0))
  def __str__(self):
    print('str called')
    return '1.0/({})'.format(self.expr)

expr = Expr.from_string('3*4-5*6')
print(expr.exec())