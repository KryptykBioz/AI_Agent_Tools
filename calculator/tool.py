# Filename: BASE/tools/installed/calculator/tool.py
"""
Calculator Tool - Simplified Architecture
Advanced calculator with expression evaluation, conversions, and statistics
"""
from typing import List, Dict, Any, Optional
from BASE.handlers.base_tool import BaseTool
import math
import re
import statistics


class MathEngine:
    """Core mathematical expression evaluator"""
    
    def __init__(self):
        # Safe mathematical functions
        self.safe_functions = {
            'sqrt': math.sqrt,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'asin': math.asin,
            'acos': math.acos,
            'atan': math.atan,
            'log': math.log10,
            'ln': math.log,
            'log10': math.log10,
            'log2': math.log2,
            'exp': math.exp,
            'abs': abs,
            'round': round,
            'ceil': math.ceil,
            'floor': math.floor,
            'factorial': math.factorial,
            'pi': math.pi,
            'e': math.e
        }
    
    def evaluate(self, expression: str) -> float:
        """
        Safely evaluate mathematical expression
        Supports: +, -, *, /, ^, %, sqrt, sin, cos, tan, log, ln, etc.
        """
        # Clean expression
        expr = expression.strip()
        
        # Replace ^ with ** for power
        expr = expr.replace('^', '**')
        
        # Replace common constants
        expr = expr.replace('pi', str(math.pi))
        expr = expr.replace('e', str(math.e))
        
        # Replace function calls with safe versions
        for func_name, func in self.safe_functions.items():
            if func_name in expr:
                # Use regex to handle function calls
                pattern = rf'\b{func_name}\s*\('
                if re.search(pattern, expr):
                    continue  # Will be evaluated in safe namespace
        
        # Create safe namespace for eval
        safe_namespace = {
            '__builtins__': {},
            **self.safe_functions
        }
        
        try:
            result = eval(expr, safe_namespace, {})
            return float(result)
        except Exception as e:
            raise ValueError(f"Invalid expression: {e}")
    
    def solve_equation(self, equation: str, variable: str) -> List[float]:
        """
        Solve simple algebraic equation for a variable
        Example: "2*x + 5 = 15" for x → [5.0]
        """
        if '=' not in equation:
            raise ValueError("Equation must contain '=' sign")
        
        left, right = equation.split('=', 1)
        left = left.strip()
        right = right.strip()
        
        # Simple linear equation solver
        # Rearrange to form: ax + b = 0
        # Move everything to left side
        combined = f"({left}) - ({right})"
        
        # Try to solve by substitution (brute force for simple cases)
        # This is a simplified solver - for complex equations, use sympy
        
        # For linear equations of form: a*x + b = 0
        try:
            # Try a range of values
            solutions = []
            for test_value in range(-1000, 1001):
                test_expr = combined.replace(variable, str(test_value))
                try:
                    result = self.evaluate(test_expr)
                    if abs(result) < 0.0001:  # Close enough to zero
                        solutions.append(float(test_value))
                except:
                    continue
            
            if solutions:
                return solutions[:1]  # Return first solution
            
            # If no integer solution, try bisection for continuous solutions
            # Test if function changes sign
            test_low = combined.replace(variable, "-1000")
            test_high = combined.replace(variable, "1000")
            
            try:
                val_low = self.evaluate(test_low)
                val_high = self.evaluate(test_high)
                
                if val_low * val_high < 0:  # Sign change indicates root
                    # Bisection method
                    low, high = -1000.0, 1000.0
                    for _ in range(50):  # 50 iterations
                        mid = (low + high) / 2
                        test_mid = combined.replace(variable, str(mid))
                        val_mid = self.evaluate(test_mid)
                        
                        if abs(val_mid) < 0.0001:
                            return [mid]
                        
                        test_low_new = combined.replace(variable, str(low))
                        val_low_new = self.evaluate(test_low_new)
                        
                        if val_low_new * val_mid < 0:
                            high = mid
                        else:
                            low = mid
                    
                    return [(low + high) / 2]
            except:
                pass
            
            raise ValueError("Could not find solution (equation may be too complex)")
        
        except Exception as e:
            raise ValueError(f"Could not solve equation: {e}")


class UnitConverter:
    """Unit conversion engine"""
    
    def __init__(self):
        # Conversion factors (to base unit)
        self.conversions = {
            # Temperature (special handling needed)
            'temperature': {
                'celsius': None,
                'fahrenheit': None,
                'kelvin': None,
                'c': None,
                'f': None,
                'k': None
            },
            
            # Length (base: meters)
            'length': {
                'meters': 1.0,
                'meter': 1.0,
                'm': 1.0,
                'kilometers': 1000.0,
                'kilometer': 1000.0,
                'km': 1000.0,
                'centimeters': 0.01,
                'centimeter': 0.01,
                'cm': 0.01,
                'millimeters': 0.001,
                'millimeter': 0.001,
                'mm': 0.001,
                'miles': 1609.34,
                'mile': 1609.34,
                'mi': 1609.34,
                'yards': 0.9144,
                'yard': 0.9144,
                'yd': 0.9144,
                'feet': 0.3048,
                'foot': 0.3048,
                'ft': 0.3048,
                'inches': 0.0254,
                'inch': 0.0254,
                'in': 0.0254
            },
            
            # Weight (base: kilograms)
            'weight': {
                'kilograms': 1.0,
                'kilogram': 1.0,
                'kg': 1.0,
                'grams': 0.001,
                'gram': 0.001,
                'g': 0.001,
                'milligrams': 0.000001,
                'milligram': 0.000001,
                'mg': 0.000001,
                'pounds': 0.453592,
                'pound': 0.453592,
                'lb': 0.453592,
                'lbs': 0.453592,
                'ounces': 0.0283495,
                'ounce': 0.0283495,
                'oz': 0.0283495,
                'tons': 1000.0,
                'ton': 1000.0
            },
            
            # Volume (base: liters)
            'volume': {
                'liters': 1.0,
                'liter': 1.0,
                'l': 1.0,
                'milliliters': 0.001,
                'milliliter': 0.001,
                'ml': 0.001,
                'gallons': 3.78541,
                'gallon': 3.78541,
                'gal': 3.78541,
                'quarts': 0.946353,
                'quart': 0.946353,
                'qt': 0.946353,
                'pints': 0.473176,
                'pint': 0.473176,
                'pt': 0.473176,
                'cups': 0.236588,
                'cup': 0.236588,
                'fluid_ounces': 0.0295735,
                'fluid_ounce': 0.0295735,
                'fl_oz': 0.0295735
            },
            
            # Speed (base: meters per second)
            'speed': {
                'mps': 1.0,
                'meters_per_second': 1.0,
                'kph': 0.277778,
                'kilometers_per_hour': 0.277778,
                'mph': 0.44704,
                'miles_per_hour': 0.44704,
                'knots': 0.514444,
                'knot': 0.514444
            },
            
            # Time (base: seconds)
            'time': {
                'seconds': 1.0,
                'second': 1.0,
                's': 1.0,
                'minutes': 60.0,
                'minute': 60.0,
                'min': 60.0,
                'hours': 3600.0,
                'hour': 3600.0,
                'hr': 3600.0,
                'h': 3600.0,
                'days': 86400.0,
                'day': 86400.0,
                'd': 86400.0,
                'weeks': 604800.0,
                'week': 604800.0,
                'wk': 604800.0,
                'years': 31536000.0,
                'year': 31536000.0,
                'yr': 31536000.0
            }
        }
    
    def convert(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert value between units"""
        from_unit = from_unit.lower().strip()
        to_unit = to_unit.lower().strip()
        
        # Special handling for temperature
        if self._is_temperature(from_unit) or self._is_temperature(to_unit):
            return self._convert_temperature(value, from_unit, to_unit)
        
        # Find category
        from_category = self._find_category(from_unit)
        to_category = self._find_category(to_unit)
        
        if from_category is None:
            raise ValueError(f"Unknown unit: {from_unit}")
        if to_category is None:
            raise ValueError(f"Unknown unit: {to_unit}")
        if from_category != to_category:
            raise ValueError(f"Cannot convert between {from_category} and {to_category}")
        
        # Convert to base unit then to target unit
        conversions = self.conversions[from_category]
        base_value = value * conversions[from_unit]
        result = base_value / conversions[to_unit]
        
        return result
    
    def _is_temperature(self, unit: str) -> bool:
        """Check if unit is temperature"""
        return unit in ['celsius', 'fahrenheit', 'kelvin', 'c', 'f', 'k']
    
    def _convert_temperature(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert temperature units"""
        # Normalize unit names
        unit_map = {'c': 'celsius', 'f': 'fahrenheit', 'k': 'kelvin'}
        from_unit = unit_map.get(from_unit, from_unit)
        to_unit = unit_map.get(to_unit, to_unit)
        
        # Convert to Celsius first
        if from_unit == 'celsius':
            celsius = value
        elif from_unit == 'fahrenheit':
            celsius = (value - 32) * 5/9
        elif from_unit == 'kelvin':
            celsius = value - 273.15
        else:
            raise ValueError(f"Unknown temperature unit: {from_unit}")
        
        # Convert from Celsius to target
        if to_unit == 'celsius':
            return celsius
        elif to_unit == 'fahrenheit':
            return celsius * 9/5 + 32
        elif to_unit == 'kelvin':
            return celsius + 273.15
        else:
            raise ValueError(f"Unknown temperature unit: {to_unit}")
    
    def _find_category(self, unit: str) -> Optional[str]:
        """Find which category a unit belongs to"""
        for category, units in self.conversions.items():
            if unit in units:
                return category
        return None
    
    def list_units(self, category: Optional[str] = None) -> Dict[str, List[str]]:
        """List available units by category"""
        if category and category.lower() != 'all':
            category = category.lower()
            if category in self.conversions:
                return {category: list(self.conversions[category].keys())}
            else:
                return {}
        else:
            # Return all categories
            return {cat: list(units.keys()) for cat, units in self.conversions.items()}


class CalculatorTool(BaseTool):
    """
    Calculator tool for mathematical operations
    No external dependencies - pure Python implementation
    """
    
    @property
    def name(self) -> str:
        return "calculator"
    
    async def initialize(self) -> bool:
        """Initialize calculator tool"""
        # Initialize engines
        self.math_engine = MathEngine()
        self.unit_converter = UnitConverter()
        
        if self._logger:
            self._logger.success("[Calculator] Initialized")
        
        return True
    
    async def cleanup(self):
        """Cleanup calculator resources"""
        if self._logger:
            self._logger.system("[Calculator] Cleaned up")
    
    def is_available(self) -> bool:
        """Check if calculator is available"""
        return hasattr(self, 'math_engine') and hasattr(self, 'unit_converter')
    
    async def execute(self, command: str, args: List[Any]) -> Dict[str, Any]:
        """
        Execute calculator command
        
        Commands:
        - calculate: Evaluate expression
        - convert: Unit conversion
        - solve: Solve equation
        - statistics: Calculate statistics
        - percentage: Calculate percentage
        - compound_interest: Calculate compound interest
        - list_units: List available units
        
        Args:
            command: Command name
            args: Command arguments
            
        Returns:
            Standardized result dict
        """
        if self._logger:
            self._logger.tool(f"[Calculator] Command: '{command}', args: {args}")
        
        # Route commands
        if command == 'calculate':
            return await self._handle_calculate(args)
        elif command == 'convert':
            return await self._handle_convert(args)
        elif command == 'solve':
            return await self._handle_solve(args)
        elif command == 'statistics':
            return await self._handle_statistics(args)
        elif command == 'percentage':
            return await self._handle_percentage(args)
        elif command == 'compound_interest':
            return await self._handle_compound_interest(args)
        elif command == 'list_units':
            return await self._handle_list_units(args)
        else:
            return self._error_result(
                f'Unknown command: {command}',
                guidance='Available: calculate, convert, solve, statistics, percentage, compound_interest, list_units'
            )
    
    async def _handle_calculate(self, args: List[Any]) -> Dict[str, Any]:
        """Handle calculate command"""
        if not args:
            return self._error_result(
                'Missing expression argument',
                guidance='Provide a mathematical expression to evaluate'
            )
        
        expression = str(args[0])
        
        try:
            result = self.math_engine.evaluate(expression)
            
            # Format result nicely
            if result == int(result):
                formatted = str(int(result))
            else:
                formatted = f"{result:.10f}".rstrip('0').rstrip('.')
            
            return self._success_result(
                f"{expression} = {formatted}",
                metadata={
                    'expression': expression,
                    'result': result,
                    'formatted': formatted
                }
            )
        
        except Exception as e:
            return self._error_result(
                str(e),
                guidance='Check expression syntax. Use +, -, *, /, ^, sqrt(), sin(), cos(), etc.'
            )
    
    async def _handle_convert(self, args: List[Any]) -> Dict[str, Any]:
        """Handle convert command"""
        if len(args) < 3:
            return self._error_result(
                'Missing arguments',
                guidance='Required: value, from_unit, to_unit'
            )
        
        try:
            value = float(args[0])
            from_unit = str(args[1])
            to_unit = str(args[2])
        except ValueError:
            return self._error_result(
                'Invalid value - must be a number',
                guidance='First argument must be numeric'
            )
        
        try:
            result = self.unit_converter.convert(value, from_unit, to_unit)
            
            # Format result
            if result == int(result):
                formatted = str(int(result))
            else:
                formatted = f"{result:.6f}".rstrip('0').rstrip('.')
            
            return self._success_result(
                f"{value} {from_unit} = {formatted} {to_unit}",
                metadata={
                    'value': value,
                    'from_unit': from_unit,
                    'to_unit': to_unit,
                    'result': result,
                    'formatted': formatted
                }
            )
        
        except Exception as e:
            return self._error_result(
                str(e),
                guidance='Use calculator.list_units to see available units'
            )
    
    async def _handle_solve(self, args: List[Any]) -> Dict[str, Any]:
        """Handle solve command"""
        if len(args) < 2:
            return self._error_result(
                'Missing arguments',
                guidance='Required: equation (with = sign), variable'
            )
        
        equation = str(args[0])
        variable = str(args[1])
        
        try:
            solutions = self.math_engine.solve_equation(equation, variable)
            
            if not solutions:
                return self._error_result(
                    'No solution found',
                    guidance='Equation may have no real solutions'
                )
            
            # Format solutions
            formatted_solutions = []
            for sol in solutions:
                if sol == int(sol):
                    formatted_solutions.append(str(int(sol)))
                else:
                    formatted_solutions.append(f"{sol:.6f}".rstrip('0').rstrip('.'))
            
            solution_str = ", ".join(formatted_solutions)
            
            return self._success_result(
                f"{variable} = {solution_str}",
                metadata={
                    'equation': equation,
                    'variable': variable,
                    'solutions': solutions,
                    'formatted': formatted_solutions
                }
            )
        
        except Exception as e:
            return self._error_result(
                str(e),
                guidance='Equation must contain = sign. Example: 2*x + 5 = 15'
            )
    
    async def _handle_statistics(self, args: List[Any]) -> Dict[str, Any]:
        """Handle statistics command"""
        if not args:
            return self._error_result(
                'Missing numbers list',
                guidance='Provide a list of numbers: [[1, 2, 3, 4, 5]]'
            )
        
        # Handle both list and individual numbers
        if isinstance(args[0], (list, tuple)):
            numbers = [float(x) for x in args[0]]
        else:
            numbers = [float(x) for x in args]
        
        if len(numbers) < 2:
            return self._error_result(
                'Need at least 2 numbers for statistics',
                guidance='Provide multiple numbers in a list'
            )
        
        try:
            stats = {
                'count': len(numbers),
                'sum': sum(numbers),
                'mean': statistics.mean(numbers),
                'median': statistics.median(numbers),
                'min': min(numbers),
                'max': max(numbers),
                'range': max(numbers) - min(numbers)
            }
            
            # Standard deviation (if enough values)
            if len(numbers) >= 2:
                stats['std_dev'] = statistics.stdev(numbers)
            
            # Mode (if exists)
            try:
                stats['mode'] = statistics.mode(numbers)
            except statistics.StatisticsError:
                stats['mode'] = None
            
            # Format output
            lines = [
                f"Count: {stats['count']}",
                f"Sum: {stats['sum']:.4f}",
                f"Mean: {stats['mean']:.4f}",
                f"Median: {stats['median']:.4f}",
                f"Min: {stats['min']:.4f}",
                f"Max: {stats['max']:.4f}",
                f"Range: {stats['range']:.4f}"
            ]
            
            if 'std_dev' in stats:
                lines.append(f"Std Dev: {stats['std_dev']:.4f}")
            
            if stats.get('mode') is not None:
                lines.append(f"Mode: {stats['mode']:.4f}")
            
            return self._success_result(
                "Statistics:\n" + "\n".join(lines),
                metadata=stats
            )
        
        except Exception as e:
            return self._error_result(
                str(e),
                guidance='Provide valid numeric values'
            )
    
    async def _handle_percentage(self, args: List[Any]) -> Dict[str, Any]:
        """Handle percentage command"""
        if len(args) < 2:
            return self._error_result(
                'Missing arguments',
                guidance='Required: part, whole'
            )
        
        try:
            part = float(args[0])
            whole = float(args[1])
        except ValueError:
            return self._error_result(
                'Invalid values - must be numbers',
                guidance='Both arguments must be numeric'
            )
        
        if whole == 0:
            return self._error_result(
                'Cannot calculate percentage - whole is zero',
                guidance='Whole value must be non-zero'
            )
        
        percentage = (part / whole) * 100
        
        return self._success_result(
            f"{part} is {percentage:.2f}% of {whole}",
            metadata={
                'part': part,
                'whole': whole,
                'percentage': percentage
            }
        )
    
    async def _handle_compound_interest(self, args: List[Any]) -> Dict[str, Any]:
        """Handle compound_interest command"""
        if len(args) < 4:
            return self._error_result(
                'Missing arguments',
                guidance='Required: principal, rate (%), time (years), frequency'
            )
        
        try:
            principal = float(args[0])
            rate = float(args[1]) / 100  # Convert percentage to decimal
            time = float(args[2])
            frequency = int(args[3])
        except ValueError:
            return self._error_result(
                'Invalid values',
                guidance='Principal, rate, and time must be numbers; frequency must be integer'
            )
        
        if frequency <= 0:
            return self._error_result(
                'Frequency must be positive',
                guidance='Use 1 for yearly, 4 for quarterly, 12 for monthly'
            )
        
        # Compound interest formula: A = P(1 + r/n)^(nt)
        amount = principal * (1 + rate/frequency) ** (frequency * time)
        interest = amount - principal
        
        return self._success_result(
            f"Principal: ${principal:.2f}\n"
            f"Interest Rate: {rate*100:.2f}% per year\n"
            f"Time: {time} years\n"
            f"Compounding: {frequency}x per year\n"
            f"Final Amount: ${amount:.2f}\n"
            f"Interest Earned: ${interest:.2f}",
            metadata={
                'principal': principal,
                'rate': rate * 100,
                'time': time,
                'frequency': frequency,
                'final_amount': amount,
                'interest_earned': interest
            }
        )
    
    async def _handle_list_units(self, args: List[Any]) -> Dict[str, Any]:
        """Handle list_units command"""
        category = args[0] if args else 'all'
        
        try:
            units = self.unit_converter.list_units(category)
            
            if not units:
                return self._error_result(
                    f'Unknown category: {category}',
                    guidance='Valid categories: temperature, length, weight, volume, speed, time, all'
                )
            
            # Format output
            lines = []
            for cat, unit_list in units.items():
                lines.append(f"\n{cat.upper()}:")
                lines.append("  " + ", ".join(unit_list))
            
            return self._success_result(
                "Available Units:" + "\n".join(lines),
                metadata={'units': units}
            )
        
        except Exception as e:
            return self._error_result(
                str(e),
                guidance='Use "all" to see all categories'
            )
    
    def get_status(self) -> Dict[str, Any]:
        """Get calculator status"""
        return {
            'available': self.is_available(),
            'features': [
                'expression_evaluation',
                'unit_conversion',
                'equation_solving',
                'statistics',
                'percentage',
                'compound_interest'
            ],
            'supported_operations': ['+', '-', '*', '/', '^', '%', 'sqrt', 'sin', 'cos', 'tan', 'log', 'ln'],
            'conversion_categories': list(self.unit_converter.conversions.keys())
        }