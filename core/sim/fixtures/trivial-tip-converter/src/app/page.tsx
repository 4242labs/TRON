import ConverterForm from "./converter-form";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center p-8 gap-8">
      <header className="text-center">
        <h1 className="text-2xl font-semibold">Trivial Tip Converter</h1>
        <p className="mt-2 text-sm text-foreground/70">
          Split a bill with tip, and convert distance / temperature units.
        </p>
      </header>
      <main className="w-full flex justify-center">
        <ConverterForm />
      </main>
    </div>
  );
}
