from .models import ModelBase
from .openai_models import GPTChat
from .codegen import CodeGen


def model_factory(
        name: str,
        model_name: str,
        **args,
    ) -> ModelBase:
    if name == 'gpt' or name == 'api':
        model = GPTChat(model_name=model_name, **args)
    elif name == 'codegen':
        model = CodeGen(model_name=model_name)
    else:
        raise NotImplementedError

    print(f'{name}: {model_name} loaded.', flush=True)
    return model
