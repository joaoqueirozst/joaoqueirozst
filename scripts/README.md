# Atualizar o gráfico de linguagens

Na raiz do repositório, com o GitHub CLI autenticado como o dono do perfil:

```bash
python3 scripts/update_languages.py
git add profile/languages.json profile/languages.svg
git commit -m "Atualiza linguagens do perfil"
git push origin main
```

O script considera todas as linguagens detectadas pelo GitHub nos repositórios
do dono do perfil, públicos e privados, incluindo forks. Soma os bytes de cada
linguagem e mostra todas individualmente. Não mede autoria individual do código.

Os arquivos gerados contêm somente linguagens e totais agregados; nomes de
repositórios, código, URLs privados e tokens não são gravados. Os dados dos
repositórios privados são atualizados ao executar o script autenticado.
