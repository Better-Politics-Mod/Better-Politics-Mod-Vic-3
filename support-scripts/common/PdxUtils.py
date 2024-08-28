class PdxUtil:
    @staticmethod
    def set_variable(name, value=True):
        if value is True:
            return {"set_variable": name}
        return {"set_variable": [{"name": name}, {"value": value}]}

    @staticmethod
    def change_variable(name, add_value):
        return {"change_variable": [{"name": name}, {"add": add_value}]}

    @staticmethod
    def if_statement(limit_conditions, *actions):
        if "limit" not in limit_conditions:
            limit_conditions = {"limit": limit_conditions}

        return {"if": [limit_conditions, *actions]}

    @staticmethod
    def pairs(*args):
        return [PdxUtil.pair(*arg) for arg in args]
    
    @staticmethod
    def pair(*arg):
        return {arg[0]: arg[1]}
    
    @staticmethod
    def not_condition(condition):
        return {"NOT": condition}
    
    @staticmethod
    def has_variable(name):
        return {"has_variable": name}
    
    @staticmethod 
    def set_list(name, *args):
        return {name: [*args]}
    
    @staticmethod
    def integer_range(min, max):
        return {"integer_range": {"min": min, "max": max}}
    
    @staticmethod
    def remove_variable(name):
        return {"remove_variable": name}
    
    @staticmethod
    def do(arg):
        return {arg: True}
    
    @staticmethod
    def add_agenda(id):
        return {
            "bpm_add_agenda": {
                "id": id
            }
        }