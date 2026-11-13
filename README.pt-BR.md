# EditAI — status da implementação

**Status: fatia inicial incompleta; não é um produto completo nem uma versão validada.**

## Recursos presentes no código

- Worker Python com diagnóstico e registro de capacidades.
- Projeto portátil v1 em JSON, imagens copiadas, caminhos relativos e verificação SHA-256.
- Exportação de animação convencional de uma foto e montagem de fotos com áudio opcional via FFmpeg.
- Edição de duração/aprovação de cena e exportação/importação de arquivo ZIP portátil, com validação contra traversal e limites de tamanho.
- Testes unitários existem, mas não foram executados nesta sessão.

## Ainda não implementado

Interface Flutter, aplicativo Android com Media3, desenho e revelação de traços, editor de timeline, ferramentas de edição geral de vídeo, legendas, gerenciador e inferência de modelos de IA, modo companion, instaladores e builds multiplataforma.

## Evidência e limitações

O código-fonte não prova que o render funciona em uma máquina específica. FFmpeg e codecs precisam ser instalados pelo usuário. Nenhum teste, render, benchmark, build ou inferência foi executado nesta sessão. Consulte `VALIDATION.md`.

## Executar

Veja `README.md` para comandos CLI e `python3 -m unittest discover -s tests -v` para os testes. Não há ainda uma interface gráfica ou artefato instalável.
