# Atualizar as linguagens do gráfico circular

Na raiz do repositório, com o GitHub CLI autenticado como o dono do perfil:

```bash
python3 scripts/update_languages.py
git add profile/languages.json profile-3d-contrib/profile-night-white.svg
git commit -m "Atualiza linguagens do perfil"
git push origin main
```

O script considera todas as linguagens detectadas pelo GitHub nos repositórios
do dono do perfil, públicos e privados, incluindo forks. Soma os bytes de cada
linguagem e mostra todas individualmente. Não mede autoria individual do código.

Os arquivos gerados contêm somente linguagens e totais agregados; nomes de
repositórios, código, URLs privados e tokens não são gravados. Os dados dos
repositórios privados são atualizados ao executar o script autenticado.

O gráfico circular integrado à imagem 3D usa esses totais, sem agrupar linguagens
em “other”. O workflow reaplica os totais salvos após cada geração da imagem 3D.
