import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

export default async function Home() {
  const users = await prisma.user.findMany();
  return (
    <main>
      <h1>Users</h1>
      <ul>
        {users.map((u) => (
          <li key={u.id}>{u.email}</li>
        ))}
      </ul>
    </main>
  );
}
