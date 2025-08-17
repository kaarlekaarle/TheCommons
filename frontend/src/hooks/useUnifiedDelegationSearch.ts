import { useState, useEffect } from "react";
import { searchPeople, searchFields } from "../api/delegationsApi";
import type { PersonSearchResult, FieldSearchResult } from "../api/delegationsApi";

export function useUnifiedDelegationSearch() {
  const [query, setQuery] = useState("");
  const [people, setPeople] = useState<PersonSearchResult[]>([]);
  const [fields, setFields] = useState<FieldSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function performSearch() {
      if (!query.trim()) {
        setPeople([]);
        setFields([]);
        setError(null);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const [peopleResults, fieldsResults] = await Promise.all([
          searchPeople(query),
          searchFields(query)
        ]);

        if (!cancelled) {
          setPeople(peopleResults);
          setFields(fieldsResults);
        }
      } catch (err) {
        if (!cancelled) {
          setError("Search failed. Please try again.");
          setPeople([]);
          setFields([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    const timeoutId = setTimeout(performSearch, 250); // 250ms debounce

    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
  }, [query]);

  return {
    query,
    setQuery,
    people,
    fields,
    loading,
    error
  };
}
