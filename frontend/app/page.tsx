export default async function Home() {
  const response = await fetch(`${process.env.API_URL}/products`);
  const data = await response.json();
  return (
    <>
      <h1>Catalog List</h1>
      <ul>
        {data.products.map((product: { id: number; name: string }) => (
          <li key={product.id}>
            {product.name}{" "}
            {
              <img
                src={`/products/${product.id}/photo`}
                alt={product.name}
                width={200}
              />
            }
          </li>
        ))}
      </ul>
    </>
  );
}
