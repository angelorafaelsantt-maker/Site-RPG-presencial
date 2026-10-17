# Livro dos Destinos — site com contas e reservas

Este projeto precisa de hospedagem Python e armazenamento persistente. Não basta abrir o HTML localmente.

## Iniciar localmente

```bash
pip install -r requirements.txt
export MASTER_SETUP_TOKEN='um-codigo-secreto-grande'
export SECRET_KEY='uma-chave-aleatoria-longa'
python server.py
```

Acesse http://localhost:5000 e use **Primeiro acesso do mestre** para cadastrar o mestre. Depois os jogadores podem criar contas.

## Publicação

Publique em um servidor com HTTPS, configure `MASTER_SETUP_TOKEN`, `SECRET_KEY`, `HTTPS=1`, `DB_PATH` apontando para um disco persistente e inicie com `gunicorn server:app --bind 0.0.0.0:$PORT`. O SQLite precisa estar em um volume persistente e em uma instância única. Faça backups do banco. A aplicação é um protótipo funcional: antes de disponibilizar publicamente, recomenda-se adicionar proteção CSRF, limitação de tentativas de login e recuperação de senha.
