# src/domain/services/data_service.py
from typing import List, Dict, Any
from datetime import date
from src.domain.entities.production import Production
from src.domain.entities.oil_price import OilPrice
from src.domain.entities.exchange_rate import ExchangeRate

class DataService:
    """
    A service class for performing data operations like filtering, aggregation, and joining.
    """

    def filter_production(self, data: List[Production], criteria: Dict[str, Any]) -> List[Production]:
        """
        Filters production data based on given criteria.
        """
        if not criteria:
            return list(data)

        filtered_data = list(data)

        for key, criterion_val in criteria.items():
            parts = key.split('__')
            attr_name = parts[0]
            operator = parts[1] if len(parts) > 1 else 'eq'

            if attr_name not in Production.model_fields:
                # print(f"Warning: Criterion key '{attr_name}' (from '{key}') is not a valid field. Skipping this criterion.")
                continue

            current_run_items = []
            for item in filtered_data:
                item_value = getattr(item, attr_name, None)
                
                actual_criterion_value = criterion_val
                if attr_name == 'reference_date' and isinstance(criterion_val, str):
                    try:
                        actual_criterion_value = date.fromisoformat(criterion_val)
                    except ValueError:
                        # Malformed date string in criterion value, this item cannot match.
                        # Effectively, this specific criterion will filter out all items if its value is a bad date string.
                        # (No item's date will equal a value that couldn't be parsed)
                        continue # Skip this item, it can't match the malformed criterion value

                match = False
                # Handle cases where item_value or actual_criterion_value might be None
                if actual_criterion_value is None:
                    if operator == 'eq':
                        match = item_value is None
                    elif operator == 'ne':
                        match = item_value is not None
                    else:
                        # Range comparisons with None are generally not well-defined or lead to False.
                        # For example, `5 > None` would raise TypeError.
                        # We'll consider them as not matching.
                        match = False
                elif item_value is None:
                    # item_value is None, but actual_criterion_value is not (due to previous block)
                    # Only 'ne' can be true if actual_criterion_value is not None. 'eq' would be false.
                    if operator == 'ne':
                         match = True # item_value is None, criterion is not None
                    else:
                         match = False
                else: # Both item_value and actual_criterion_value are not None
                    if operator == 'eq':
                        match = item_value == actual_criterion_value
                    elif operator == 'ne':
                        match = item_value != actual_criterion_value
                    # For type safety with comparison operators, ensure types are compatible if possible
                    # Pydantic model should ensure item_value has a comparable type.
                    # We assume actual_criterion_value is also of a comparable type or conversion handled (like date).
                    elif operator == 'gt':
                        try:
                            match = item_value > actual_criterion_value
                        except TypeError: # Handles incomparable types e.g. int > str
                            match = False
                    elif operator == 'ge':
                        try:
                            match = item_value >= actual_criterion_value
                        except TypeError:
                            match = False
                    elif operator == 'lt':
                        try:
                            match = item_value < actual_criterion_value
                        except TypeError:
                            match = False
                    elif operator == 'le':
                        try:
                            match = item_value <= actual_criterion_value
                        except TypeError:
                            match = False
                
                if match:
                    current_run_items.append(item)
            
            filtered_data = current_run_items
            if not filtered_data: # Optimization: if list becomes empty, no further filtering needed
                break
                
        return filtered_data

    def aggregate_production(
        self,
        data: List[Production],
        group_by_fields: List[str],
        aggregation_functions: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Aggregates production data by specified fields and functions using Polars.
        """
        if not data:
            return []

        try:
            import polars as pl
            from polars import PolarsError
        except ImportError:
            # This path should ideally be handled by ensuring polars is in the environment.
            # If running in an environment where pip install can be triggered, it would go here.
            # For this context, assume polars is available or raise an error.
            print("Polars library not found. Please install it: pip install polars")
            # Depending on strict error handling requirements, could raise an exception:
            raise ImportError("Polars library is required for aggregation but not found.")


        # Convert List[Production] to List[Dict] for DataFrame creation
        # This ensures that Pydantic models are correctly serialized.
        try:
            dict_data = [item.model_dump() for item in data]
            df = pl.DataFrame(dict_data)
        except Exception as e: # Catch potential errors during Pydantic serialization or DataFrame creation
            print(f"Error converting data to Polars DataFrame: {e}")
            return []

        if df.is_empty():
            return []

        # Validate group_by_fields
        valid_group_by_fields = [field for field in group_by_fields if field in df.columns]
        if not valid_group_by_fields and group_by_fields: # Some group_by_fields were provided, but none are valid
            print(f"Warning: None of the specified group_by_fields exist in the data: {group_by_fields}. "
                  f"Available columns: {df.columns}")
            # Depending on requirements, could return df.select(valid_group_by_fields).to_dicts() or []
            # If no valid group_by_fields, aggregation as specified is not possible.
            # Consider what to return: empty list, or error, or data grouped by nothing (if agg_funcs exist).
            # For now, let's return empty list if user specified group_by fields but none were valid.
            return []
        
        # If group_by_fields was initially empty, valid_group_by_fields will be empty.
        # Polars group_by with an empty list groups nothing and applies aggs to all rows.

        # Construct aggregation expressions
        agg_exprs = []
        available_columns = df.columns
        for col_name, func_name in aggregation_functions.items():
            if col_name not in available_columns:
                print(f"Warning: Column '{col_name}' for aggregation not found. Skipping.")
                continue
            
            # Check if the aggregation function is valid for a Polars expression
            # Common functions: sum, mean, min, max, first, last, count, std, var, median
            # More robust check: hasattr(pl.Expr, func_name)
            if not hasattr(pl.col(col_name), func_name):
                print(f"Warning: Aggregation function '{func_name}' is not a valid Polars expression method for column '{col_name}'. Skipping.")
                continue
            
            try:
                # Dynamically call the method on the expression
                expr = getattr(pl.col(col_name), func_name)()
                agg_exprs.append(expr.alias(f"{col_name}_{func_name}"))
            except Exception as e: # Catch errors during expression creation (e.g. func_name not callable)
                print(f"Error creating aggregation expression for {col_name}_{func_name}: {e}")
                continue
        
        if not agg_exprs:
            print("Warning: No valid aggregation expressions could be constructed.")
            # If there are group_by fields, return distinct combinations of them
            if valid_group_by_fields:
                return df.select(valid_group_by_fields).unique().to_dicts()
            else: # No group_by fields and no aggregations, what to return? An empty list seems safest.
                return []

        try:
            if valid_group_by_fields:
                aggregated_df = df.group_by(valid_group_by_fields, maintain_order=True).agg(agg_exprs)
            else:
                # No group_by fields, aggregate over the whole DataFrame
                # Ensure selected columns are only the aggregated ones, as group_by keys aren't present
                aggregated_df = df.select(agg_exprs)
                
            return aggregated_df.to_dicts()
        
        except PolarsError as e:
            print(f"Polars error during aggregation: {e}")
            return []
        except Exception as e: # Catch any other unexpected errors
            print(f"An unexpected error occurred during aggregation: {e}")
            return []

    def join_data(
        self,
        production_data: List[Production],
        price_data: List[OilPrice],
        exchange_data: List[ExchangeRate]
    ) -> List[Dict[str, Any]]:
        """
        Joins production, oil price, and exchange rate data based on common keys (e.g., reference_date) using Polars.
        """
        if not production_data:
            return []

        try:
            import polars as pl
            from polars import PolarsError # Specific Polars errors
        except ImportError:
            print("Polars library not found. Please install it: pip install polars")
            raise ImportError("Polars library is required for join operations but not found.")

        try:
            # Convert production data
            dict_production_data = [p.model_dump() for p in production_data]
            if not dict_production_data: # Should be caught by the initial check, but as a safeguard
                 return []
            joined_df = pl.DataFrame(dict_production_data)
            if joined_df.is_empty(): # Double check after DataFrame conversion
                return []

            # Join with price data
            if price_data:
                dict_price_data = [p.model_dump() for p in price_data]
                if dict_price_data: # Ensure list is not empty after model_dump
                    price_df = pl.DataFrame(dict_price_data)
                    if not price_df.is_empty() and "reference_date" in price_df.columns:
                        # Suffixes for overlapping columns other than 'reference_date' are handled by Polars automatically
                        joined_df = joined_df.join(price_df, on="reference_date", how="left")
                    elif "reference_date" not in price_df.columns and not price_df.is_empty():
                        print("Warning: 'reference_date' column missing in price_data. Skipping join with price_data.")
            
            # Join with exchange rate data
            if exchange_data:
                dict_exchange_data = [e.model_dump() for e in exchange_data]
                if dict_exchange_data: # Ensure list is not empty after model_dump
                    exchange_df = pl.DataFrame(dict_exchange_data)
                    if not exchange_df.is_empty() and "reference_date" in exchange_df.columns:
                        # Suffixes for overlapping columns other than 'reference_date' are handled by Polars automatically
                        joined_df = joined_df.join(exchange_df, on="reference_date", how="left")
                    elif "reference_date" not in exchange_df.columns and not exchange_df.is_empty():
                         print("Warning: 'reference_date' column missing in exchange_data. Skipping join with exchange_data.")

            return joined_df.to_dicts()

        except PolarsError as e:
            print(f"Polars error during join operation: {e}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred during join operation: {e}")
            return []

# Example usage (for illustration, not part of the class itself):
# if __name__ == '__main__':
#     from datetime import date
#     # Sample data
#     prod_data = [
#         Production(reference_date=date(2023, 1, 1), oil_prod=1000, gas_prod=500, water_prod=200, well_code="W1"),
#         Production(reference_date=date(2023, 1, 1), oil_prod=1500, gas_prod=600, water_prod=250, well_code="W2"),
#     ]
#     price_data = [
#         OilPrice(reference_date=date(2023, 1, 1), field_name="FieldA", field_code="F1", price=70.5),
#     ]
#     exchange_data = [
#         ExchangeRate(reference_date=date(2023, 1, 1), rate=5.25),
#     ]

#     service = DataService()

#     # Filter example (conceptual)
#     # filtered = service.filter_production(prod_data, {"well_code": "W1"})
#     # print(f"Filtered: {filtered}") # This would be empty list due to pass

#     # Aggregate example (conceptual)
#     # aggregated = service.aggregate_production(prod_data, ["well_code"], {"oil_prod": "sum"})
#     # print(f"Aggregated: {aggregated}") # This would be empty list due to pass
    
#     # Join example (conceptual)
#     # joined = service.join_data(prod_data, price_data, exchange_data)
#     # print(f"Joined: {joined}") # This would be empty list due to pass
