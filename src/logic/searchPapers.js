export function searchPapers({ query, papers }) {
  const normalizedQuery = (query || "").trim().toLowerCase();
  const library = Array.isArray(papers) ? papers : [];

  if (!normalizedQuery) {
    return library.slice(0, 4);
  }

  return library.filter((paper) => {
    const searchableText = [
      paper.title,
      paper.authors,
      paper.abstract,
      paper.methodology,
      ...(Array.isArray(paper.keywords) ? paper.keywords : [])
    ]
      .join(" ")
      .toLowerCase();

    return searchableText.includes(normalizedQuery);
  });
}

export default searchPapers;
