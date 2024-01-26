# python

## Steps to make a commit:

     git init
     git add .\README.md
     git commit -m 'first commit'
     git branch -M main
     git remote add origin https://github.com/crmills100/python.git
     git push -u origin main
     git commit -m 'change encoding' .\README.md
     git push -u origin main



     pipenv shell
     python {script_name}


## For a virtual environment:

     virtualenv -p python3 {path_to_virtenv}
     cd {path_to_virtualenv}
     .\Scripts\activate 
     # run pip install for any modules
     #   example: pip install pyautogui
     python {path_to_python_script}

