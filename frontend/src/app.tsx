import RepoInput from "./components/RepoInput";

function App() {
  return (
    <RepoInput
      onSubmit={(url) => console.log(url)}
      isLoading={false}
    />
  );
}

export default App;