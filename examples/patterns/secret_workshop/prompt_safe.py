"""Supplied narrow prevention: choose task context; never include runtime secrets."""
def build_prompt(question, context, runtime):
    return [{'role':'user','content':f'{question}\nContext: {context}'}]
