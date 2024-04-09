import {Table, TableHeader, TableColumn, TableBody, TableRow, TableCell, Pagination, Input, Spinner, Button} from "@nextui-org/react";
import {useAsyncList} from "@react-stately/data";
import React, { useState } from 'react';
import { Container, Row, Col } from "reactstrap";
import { Accordion, AccordionItem } from "@nextui-org/accordion";
import Link from 'next/link';
import {SearchIcon} from './SearchIcon';

export default function ArticleListTable({stream_id,category_id,node_id}:any) {
  const [isLoading, setIsLoading] = useState(true);
  const [filterValue, setFilterValue] = React.useState("");
  const [columns, setColumns] = useState([
    {name: "Publication", uid: "name"},
    {name: "Created at", uid: "created_at"},
    {name: "Actions", uid: "actions"},
  ]);

  const back_link_arr = node_id.split(".")
  back_link_arr.pop()
  const back_link = back_link_arr.join(".")
  
  const [stream, setStream] = React.useState("");
  const [resource, setResource] = React.useState("");
  const [category, setCategory] = React.useState("")
  const [rowsPerPage, setRowsPerPage] = React.useState(3);
  const [page, setPage] = React.useState(1);

  const hasSearchFilter = Boolean(filterValue);

  const itemClasses = {
    base: "py-0 w-full",
    title: "font-bold text-small",
    trigger: "px-2 py-0 data-[hover=true]:bg-default-100 rounded-lg h-10 flex items-center",
    indicator: "text-small",
    content: "light px-2",
  };

  let list = useAsyncList({
    async load({signal}) {
      let res = await fetch('http://localhost:8000/api/category/'+stream_id+'/'+category_id, {
        signal,
      });
      let json = await res.json();
      setIsLoading(false);
      setStream(json[0]["negotiation_stream"])
      setResource(json[0]["category"].split("-")[0] + "Resources");
      setCategory(json[0]["category"].split("-")[1])
      return {
        items: json,
      };
    },
    async sort({items, sortDescriptor}) {
      return {
        items: items.sort((a, b) => {
          let first = a[sortDescriptor.column];
          let second = b[sortDescriptor.column];
          let cmp = (parseInt(first) || first) < (parseInt(second) || second) ? -1 : 1;

          if (sortDescriptor.direction === "descending") {
            cmp *= -1;
          }

          return cmp;
        }),
      };
    },
  });

  const filteredItems = React.useMemo(() => {
    let filteredArticles = [...list.items];

    if (hasSearchFilter) {
      filteredArticles = filteredArticles.filter((article) =>
        article.condensed_summary.toLowerCase().includes(filterValue.toLowerCase()) ||
        article.name.toLowerCase().includes(filterValue.toLowerCase())
      );
    }

    return filteredArticles;
  }, [list.items, filterValue]);

  const pages = Math.ceil(list.items.length / rowsPerPage);

  const items = React.useMemo(() => {
    const start = (page - 1) * rowsPerPage;
    const end = start + rowsPerPage;

    return filteredItems.slice(start, end);
  }, [page, filteredItems, rowsPerPage]);


  const onRowsPerPageChange = React.useCallback((e) => {
    setRowsPerPage(Number(e.target.value));
    setPage(1);
  }, []);


  const onSearchChange = React.useCallback((value) => {
    if (value) {
      setFilterValue(value);
      setPage(1);
    } else {
      setFilterValue("");
    }
  }, []);


  const topContent = React.useMemo(() => {
    return (
      <div>
        <nav className="breadcrumbs">
          <Link href={{
            pathname: '/',
            query: {
              back_link: stream_id
            }
          }} className="breadcrumbs__item">
            ← {stream}
          </Link>
          <Link href={{
            pathname: '/',
            query: {
              back_link: back_link
            }
          }} className="breadcrumbs__item">
            ← {resource}
          </Link>
          <a className="breadcrumbs__item is-active">{category}</a> 
        </nav>
        <div>
          <Input
            isClearable
            classNames={{
              base: "w-full sm:max-w-[44%]",
              inputWrapper: "border-1",
              input: [
                "fontsmall",
              ],
            }}
            placeholder="Search by summary text..."
            size="sm"
            startContent={<SearchIcon className="text-default-300" />}
            value={filterValue}
            variant="bordered"
            onClear={() => setFilterValue("")}
            onValueChange={onSearchChange}
          />
        </div>
      </div>
    );
  }, [
    filterValue,
    onSearchChange,
    onRowsPerPageChange,
    list.items.length,
    hasSearchFilter,
  ]);


  const bottomContent = React.useMemo(() => {
    return (
      <div>
      <div className="flex justify-between items-center">
        <label className="flex items-center text-default-400 text-small">
          Rows per page:
          <select
            className="bg-transparent outline-none text-default-400 text-small"
            onChange={onRowsPerPageChange}
          >
            <option value="3">3</option>
            <option value="5">5</option>
            <option value="10">10</option>
            <option value="15">15</option>
          </select>
        </label>
      </div>
      <div className="py-2 px-2 flex justify-between items-center">
        <Pagination
          showControls
          classNames={{
            cursor: "bg-foreground text-background",
          }}
          color="default"
          isDisabled={hasSearchFilter}
          page={page}
          total={pages}
          variant="light"
          onChange={setPage}
        />
      </div>
      </div>
    );
  }, [list.items.length, page, pages, hasSearchFilter]);


  const renderCell = React.useCallback((article:any, columnKey:any) => {
    const cellValue = article[columnKey];

    switch (columnKey) {
      case "name":
        return (
          <div className="flex flex-col">
            <Accordion isCompact defaultExpandedKeys={["item"]} itemClasses={itemClasses}>
              <AccordionItem key="item" title={article.name} className="fontsmall">{article.condensed_summary}</AccordionItem>
            </Accordion>
          </div>
        );
      case "created_at":
        return (
          <div className="flex flex-col">
            <p className="text-bold text-sm fontsmall">{article.created_at}</p>
          </div>
        );
      case "actions":
        return (
          <div className="relative flex items-center gap-2">
            <Button 
              color="default" 
              size="sm"
              href={"/article/"+article.id}
              as={Link}
            >
              View Detail
            </Button>
            <Button 
              color="primary" 
              size="sm" 
              href={article.url}
              as={Link}
              variant="solid"
            >
              Visit
            </Button>
          </div>
        );
      default:
        return cellValue;
    }
  }, []);

  return (
    <Container className="light">
      <Row className="mt-6">
        <Col className="md-6">
          <Table className="max-w-[1200px] center"
            aria-label="Article List"
            title="Article List"
            sortDescriptor={list.sortDescriptor}
            onSortChange={list.sort}
            bottomContent={bottomContent}
            topContent={topContent}
          >
            <TableHeader columns={columns}>
              {(column) => (
                <TableColumn 
                  key={column.uid} 
                  align={column.uid === "actions" ? "center" : "start"} 
                  allowsSorting = {column.uid === "created_at" ? true : false}
                >
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
                <TableRow key={item.name} className="light">
                  {(columnKey) => <TableCell>{renderCell(item, columnKey)}</TableCell>}
                </TableRow>
              )}
            </TableBody>
          </Table>
        </Col>
      </Row>
    </Container>
  );
}