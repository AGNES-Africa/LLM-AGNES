"use client";

import React from "react";
import {Table, TableHeader, TableColumn, TableBody, TableRow, TableCell, getKeyValue, Spinner} from "@nextui-org/react";
import {useAsyncList} from "@react-stately/data";

export default function ArticleListTable({category_id}) {
  const [isLoading, setIsLoading] = React.useState(true);

  let list = useAsyncList({
    async load({signal}) {
      let res = await fetch('http://localhost:8000/api/category/'+category_id, {
        signal,
      });
      let json = await res.json();
      setIsLoading(false);
      console.log(json)
      return {
        items: json,
      };
    }
  });

  return (
    <Table 
      aria-label="Article List"
      classNames={{
        table: "min-h-[300px]",
      }}
    >
      <TableHeader>
        <TableColumn key="name" allowsSorting>
          Title
        </TableColumn>
        <TableColumn key="created_at" allowsSorting>
          Created
        </TableColumn>
      </TableHeader>
      <TableBody
        items={list.items} 
        isLoading={isLoading}
        loadingContent={<Spinner label="Loading..." />}
      >
        {(item) => (
          <TableRow key={item.name}>
            {(columnKey) => <TableCell>{getKeyValue(item, columnKey)}</TableCell>}
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}