import React from "react";
import {Table, TableHeader, TableColumn, TableBody, TableRow, TableCell, Pagination, Tooltip, getKeyValue, Spinner, Button} from "@nextui-org/react";
import {useAsyncList} from "@react-stately/data";

export default function ArticleListTable({stream_id,category_id}:any) {
  const [isLoading, setIsLoading] = React.useState(true);
  const columns = [
    {name: "NAME", uid: "name"},
    {name: "CREATED AT", uid: "created_at"},
    {name: "ACTIONS", uid: "actions"},
  ];

  let list = useAsyncList({
    async load({signal}) {
      let res = await fetch('http://localhost:8000/api/category/'+stream_id+'/'+category_id, {
        signal,
      });
      let json = await res.json();
      setIsLoading(false);
      return {
        items: json,
      };
    }
  });

  const renderCell = React.useCallback((article:any, columnKey:any) => {
    const cellValue = article[columnKey];

    switch (columnKey) {
      case "name":
        return (
          <div className="flex flex-col"><a href={article.url}>{article.name}</a></div>
        );
      case "created_at":
        return (
          <div className="flex flex-col">
            <p className="text-bold text-sm">{article.created_at}</p>
          </div>
        );
      case "actions":
        return (
          <div className="relative flex items-center gap-2">
            <Button color="default" size="sm">
              View Summary
            </Button>
            <Button color="primary" size="sm" href={article.url}>
              Visit
            </Button>
          </div>
        );
      default:
        return cellValue;
    }
  }, []);

  const [page, setPage] = React.useState(1);
  const rowsPerPage = 5;

  const pages = Math.ceil(list.items.length / rowsPerPage);

  const items = React.useMemo(() => {
    const start = (page - 1) * rowsPerPage;
    const end = start + rowsPerPage;

    return list.items.slice(start, end);
  }, [page, list.items]);

  return (
    <Table 
      aria-label="Article List"
      classNames={{
        table: "min-h-[300px]",
      }}
      bottomContent={
        <div className="flex w-full justify-center">
          <Pagination
            isCompact
            showControls
            showShadow
            color="secondary"
            page={page}
            total={pages}
            onChange={(page) => setPage(page)}
          />
        </div>
      }
    >
      <TableHeader columns={columns}>
        {(column) => (
          <TableColumn key={column.uid} align={column.uid === "actions" ? "center" : "start"}>
            {column.name}
          </TableColumn>
        )}
      </TableHeader>
      <TableBody
        items={items} 
        isLoading={isLoading}
        loadingContent={<Spinner label="Loading..." />}
      >
        {(item:any) => (
          <TableRow key={item.name}>
            {(columnKey) => <TableCell>{renderCell(item, columnKey)}</TableCell>}
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}