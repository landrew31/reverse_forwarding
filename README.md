### 0. Install `pyenv`.
If you have pyenv on your computer, skip this step. Otherwise, follow next:

- Execute in terminal `curl -L https://raw.githubusercontent.com/pyenv/pyenv-installer/master/bin/pyenv-installer | bash`
- Add lines in ~/.bashrc:
`export PATH="~/.pyenv/bin:$PATH"`
`eval "$(pyenv init -)"`
`eval "$(pyenv virtualenv-init -)"`
- Execute in terminal `exec bash`
- Execute in terminal `pyenv update`

### 1. Create `virtualenv`:
Create `virtualenv` using `pyenv`:
- Install appropriate version of `python`: `pyenv install 3.6.4`
- Create `virtualenv` named `payment-testing-firewall`: `pyenv virtualenv 3.6.4 payment-testing-firewall`

### 2. Clone project:
- Execute being in `/workspace`: `git clone git@gitlab.uaprom:crm-team/payment-testing-firewall.git`

### 2. Run service:
- Go to project path (execute being in `/workspace`: `cd payment-testing-firewall`
- Launch `virtualenv`: `pyenv local payment-testing-firewall`
- Run: `python3 app.py`
