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
em “other”. Após regenerar a imagem 3D, execute `python3 scripts/update_donut.py`
para reaplicar os totais salvos ao gráfico circular.

## Atualizar as estatísticas do perfil

O cartão `profile/stats-<versão>.svg` é gerado por `scripts/update_stats.py`, consultando a
API GraphQL com o GitHub CLI autenticado como o dono do perfil. O layout original
do GitHub Profile Summary Cards, tema `github_dark`, é preservado integralmente:
título, dimensões, cores, ícones, logotipo e as mesmas cinco linhas. Somente os
valores numéricos são atualizados, sem rodapé ou texto de atualização. O serviço externo anterior não tinha acesso
aos PRs dos repositórios privados do usuário.

- **Total PRs:** todos os PRs de autoria do usuário acessíveis à credencial,
  incluindo abertos, fechados e incorporados, públicos e privados.
- **Total Issues:** issues de autoria do usuário acessíveis à credencial.
- **Commits:** contribuições de commits reconhecidas pelo GitHub nos últimos
  12 meses; não é o total histórico de commits.
- **Estrelas:** soma dos repositórios públicos próprios que não são forks, com
  paginação. **Repositórios com contribuições:** somente públicos, como no cartão
  anterior.

O arquivo publica apenas totais agregados. Não grava nomes de repositórios
privados, títulos de PRs, código ou credenciais. O modelo original está em
`scripts/templates/stats-github-dark.svg`, com a licença MIT do
[projeto original](https://github.com/vn7n24fzkq/github-profile-summary-cards)
em `scripts/templates/LICENSE-summary-cards.txt`.

### Configuração única para atualizar pelo GitHub Actions

O workflow `.github/workflows/profile-stats.yml` consulta os dados a cada hora,
no minuto 23, e permite execução manual. O computador local pode estar desligado.
O horário pode sofrer atrasos do GitHub. Quando os números mudam, o script também
salva a imagem com um novo nome e ajusta sua referência no README, sem depender
de parâmetros na URL para renovar o cache. O cartão anterior é removido, mantendo
uma única imagem. A versão usa o conteúdo da imagem, sem mostrar data ou horário
no cartão. Atualizar ao abrir o perfil não dispara uma nova consulta.

1. Crie um [personal access token classic](https://github.com/settings/tokens/new)
   na conta do perfil, com um nome como `Estatisticas do perfil`, validade definida
   (por exemplo, 90 dias) e escopo `repo`. Esse escopo é amplo e inclui escrita;
   o script o utiliza somente para consultas. O uso do token classic neste caso
   atende também aos repositórios privados de outro usuário nos quais você é
   colaborador. Não é necessário habilitar `workflow`, `admin` ou `delete_repo`.
2. Abra [Actions secrets deste repositório](https://github.com/joaoqueirozst/joaoqueirozst/settings/secrets/actions).
   Clique em **New repository secret**, use o nome `PROFILE_STATS_TOKEN`, cole o
   token no campo **Secret** e salve. O valor não deve ir no README, no código,
   nos commits ou em mensagens de chat.
3. Abra [o workflow das estatísticas](https://github.com/joaoqueirozst/joaoqueirozst/actions/workflows/profile-stats.yml),
   clique em **Run workflow**, selecione `main` e confirme **Run workflow**.
4. Ao terminar, confira os valores no cartão indicado pelo README. As próximas consultas serão agendadas
   automaticamente, e um commit só é criado quando os valores mudam.
   Renove o secret quando o token
   expirar. Sem secret, o workflow avisa no resumo e mantém o cartão existente;
   uma credencial inválida faz a execução falhar sem substituir a imagem.

O `GITHUB_TOKEN` automático fica limitado a este repositório e não consegue ler
os PRs privados de outros projetos. Ele é usado somente para publicar a imagem;
o token pessoal fica disponível apenas na etapa de consulta. Não há envio do
token ao serviço externo que fornecia o cartão anterior.

Caso o repositório público fique sem atividade por 60 dias, o GitHub pode desativar
o agendamento; reative o workflow na aba Actions se isso acontecer. Este workflow
atualiza somente o cartão numérico. O gráfico 3D mantém seu agendamento diário e
as linguagens mantêm o procedimento descrito acima.

### Atualização manual no computador

Com o `gh` autenticado como `joaoqueirozst` e com acesso aos projetos privados:

```bash
python3 scripts/update_stats.py
git add -A -- profile README.md
git commit -m "Atualiza estatísticas do perfil"
git push origin main
```

### Referências

- [Permissões do GITHUB_TOKEN](https://docs.github.com/en/actions/concepts/security/github_token)
- [Tokens pessoais e limitações para colaboradores](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [Agendamento de workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
