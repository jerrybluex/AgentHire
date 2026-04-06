interface HeaderProps {
  title: string;
  description?: string;
}

export default function Header({ title, description }: HeaderProps) {
  return (
    <header className="mb-8">
      <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
      {description && (
        <p className="text-gray-500 mt-1">{description}</p>
      )}
    </header>
  );
}
