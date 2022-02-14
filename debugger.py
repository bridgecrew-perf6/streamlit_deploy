from streamlit import bootstrap

real_script = 'main_script.py'

bootstrap.run(real_script, f'main.py {real_script}', [], {})
