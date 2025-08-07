# AI Ops — Operator Playbook

- Always use Prisma Client, no raw SQL in Next.js
- For DB changes: edit schema.prisma, run `make migrate`
- Review all new migrations in PR/code review
- Document all model changes
- Run `make studio` to use Prisma Studio at :5555
- Always use env vars for DB/config (never hardcode secrets)