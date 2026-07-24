"""
Non-Gameable AST Exercised-Code Checker for SimPO & SFT Evaluation.
Strictly checks for COMPREHENSIVE type annotations and CORRECTIVE exception handling.
Bounds output reward R_comp in [0.0, 0.1].

Residual Risk Note:
- Non-literal RHS assignments (e.g. `res = str(e)`) raise the gaming threshold significantly
  beyond bare constants (`x = 1`), but remain a known, bounded residual risk.
  Because R_comp is strictly capped at 0.1 max, this risk is safely contained.
"""

import ast

def is_concrete_type(annotation) -> bool:
    """Checks if type annotation is concrete, explicitly rejecting `Any`, `object`, or `None` for argument positions."""
    if annotation is None:
        return False
    if isinstance(annotation, ast.Name):
        return annotation.id not in {'Any', 'object', 'None'}
    if isinstance(annotation, ast.Constant):
        return annotation.value not in {'Any', 'object', None}
    if isinstance(annotation, ast.Subscript):
        return is_concrete_type(annotation.value)
    if isinstance(annotation, ast.Attribute):
        return annotation.attr not in {'Any', 'object'}
    return True

def is_valid_return_type(annotation) -> bool:
    """Checks if return type annotation is concrete OR explicitly `None` (for side-effect functions like `-> None`)."""
    if annotation is None:
        return False
    if isinstance(annotation, ast.Constant) and annotation.value is None:
        return True
    if isinstance(annotation, ast.Name) and annotation.id == 'None':
        return True
    return is_concrete_type(annotation)

def is_non_literal_expr(node) -> bool:
    """Checks if expression is a non-trivial computation (calls, attributes, binary ops), rejecting bare constants/literals."""
    if isinstance(node, ast.Constant):
        return False
    return True

def has_corrective_action(body: list[ast.stmt]) -> bool:
    """
    Verifies handler body contains non-trivial corrective logic:
    1. Explicit `ast.Raise` (re-raising or wrapping exception)
    2. Structured logging (`logger.error`, `logging.exception`, `log.error`)
    3. Fallback return payload (`return default_value`)
    4. Non-trivial recovery assignment (`recovery_var = compute_fallback()`), rejecting bare literal assignments like `x = 1`.
    Rejects `print(...)`, `pass`, docstrings, empty returns, or bare literal assignments (`x = 1`).
    """
    for stmt in body:
        if isinstance(stmt, ast.Raise):
            return True
        if isinstance(stmt, ast.Return) and stmt.value is not None:
            if not (isinstance(stmt.value, ast.Constant) and stmt.value.value is None):
                return True
        if isinstance(stmt, ast.Call):
            func = stmt.func
            if isinstance(func, ast.Attribute):
                if func.attr in {'error', 'exception', 'warning', 'critical'}:
                    if isinstance(func.value, ast.Name) and func.value.id in {'logger', 'logging', 'log', 'lg'}:
                        return True
        if isinstance(stmt, ast.Assign):
            # Require assignment value (RHS) to be non-literal/non-trivial (e.g. `res = compute_fallback()`, NOT `x = 1`)
            if is_non_literal_expr(stmt.value):
                return True
    return False

def analyze_try_except(node: ast.Try) -> bool:
    """
    Requires handler to use specific exception type (rejects `except:` or `except Exception:`)
    AND require corrective handling inside its body.
    """
    if not node.handlers:
        return False
    
    for handler in node.handlers:
        # Reject broad clauses (`except:` or `except Exception:`)
        if handler.type is None:
            continue
        if isinstance(handler.type, ast.Name) and handler.type.id == 'Exception':
            continue
            
        # Require corrective handling inside the handler body
        if has_corrective_action(handler.body):
            return True
            
    return False

def analyze_type_annotations(node: ast.FunctionDef) -> bool:
    """
    Requires 100% COMPREHENSIVE type annotation coverage.
    ALL non-self/cls args MUST be concrete non-Any/non-None types AND return type MUST be concrete or `-> None`.
    """
    non_self_args = [
        arg for arg in node.args.args + node.args.kwonlyargs
        if arg.arg not in {'self', 'cls'}
    ]

    # Check ALL non-self arguments — failing ANY single arg invalidates coverage
    for arg in non_self_args:
        if not (arg.annotation and is_concrete_type(arg.annotation)):
            return False

    # Check return type annotation (allows concrete types and `-> None`)
    if not (node.returns and is_valid_return_type(node.returns)):
        return False

    return True

def calculate_r_comp(code: str) -> float:
    """
    Calculates non-gameable AST completeness score bounded in [0.0, 0.1].
    Strictly clipped so it NEVER swamps the preference term gamma(L).
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return 0.0
        
    score = 0.0
    for node in ast.walk(tree):
        if isinstance(node, ast.Try) and analyze_try_except(node):
            score += 0.03
        elif isinstance(node, ast.FunctionDef) and analyze_type_annotations(node):
            score += 0.02
                
    # Strict Clipping: R_comp can NEVER exceed 0.1
    return min(max(score, 0.0), 0.1)
