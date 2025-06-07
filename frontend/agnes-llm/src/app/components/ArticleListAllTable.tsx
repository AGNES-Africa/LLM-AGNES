import {Table, TableHeader, TableColumn, TableBody, TableRow, TableCell, Pagination, Input, Spinner, Select, SelectItem, Button} from "@nextui-org/react";
import {useAsyncList} from "@react-stately/data";
import React, { useState } from 'react';
import { Container, Row, Col } from "reactstrap";
import { Accordion, AccordionItem } from "@nextui-org/accordion";
import Link from 'next/link';
import {SearchIcon} from './SearchIcon';

export default function ArticleListAllTable({stream_id,category_id}:any) {
  const [isLoading, setIsLoading] = useState(true);
  const [filterValue, setFilterValue] = React.useState("");
  const [streamValue, setStreamValue] = React.useState("");
  const [columns, setColumns] = useState([
    {name: "#", uid: "number"},
    {name: "Publication", uid: "name"},
    {name: "Created at", uid: "created_at"},
    {name: "Actions", uid: "actions"},
  ]);
  const [listCp, setListCp] = useState(
    {items:[]}
  )

  const [rowsPerPage, setRowsPerPage] = React.useState(3);
  const [page, setPage] = React.useState(1);

  const hasSearchFilter = Boolean(filterValue);
  const hasStreamFilter = Boolean(streamValue);

  const itemClasses = {
    base: "py-0 w-full",
    title: "font-bold text-small",
    trigger: "px-2 py-0 data-[hover=true]:bg-default-100 rounded-lg h-10 flex items-center",
    indicator: "text-small",
    content: "light px-2",
  };

  let list = useAsyncList({
    async load({signal}) {
      let res = await fetch('https://agnes-llm-backend.azurewebsites.net/api/articles', {
        signal,
      });
      let json = await res.json();
      setIsLoading(false);
      return {
        items: json,
      };
    },
    async sort({items, sortDescriptor}:any) {
      return {
        items: items.sort((a:any, b:any) => {
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

    if(hasStreamFilter){
        filteredArticles = filteredArticles.filter((article:any) =>
            article.negotiation_stream_id === parseInt(streamValue)
        );
    }

    if (hasSearchFilter) {
      filteredArticles = filteredArticles.filter((article:any) =>
        article.condensed_summary.toLowerCase().includes(filterValue.toLowerCase()) ||
        article.name.toLowerCase().includes(filterValue.toLowerCase())
      );
    }

    return filteredArticles;
  }, [list.items, filterValue, streamValue]);

  const pages = Math.ceil(list.items.length / rowsPerPage);

  const items = React.useMemo(() => {
    const start = (page - 1) * rowsPerPage;
    const end = start + rowsPerPage;

    return filteredItems.slice(start, end);
}, [filteredItems, page, rowsPerPage]);


  const onRowsPerPageChange = React.useCallback((e:any) => {
    setRowsPerPage(Number(e.target.value));
    setPage(1);
  }, []);


  const onSearchChange = React.useCallback((value:any) => {
    if (value) {
      setFilterValue(value);
      setPage(1);
    } else {
      setFilterValue("");
    }
  }, []);

  const onStreamSelect = React.useCallback((value:any) => {
    setStreamValue(value.currentKey)
    setPage(1)
  }, []); 


const topContent = React.useMemo(() => {
  const streamNames = {
    '1': 'Agriculture',
    '2': 'Gender', 
    '3': 'Finance',
    '4': 'Adaptation',
    '5': 'IPCC'
  };
  
  return (
    <div>
      <div className="flex justify-between items-center">
        <Select size="sm" color="primary"
            label="Climate Action Stream" 
            className="max-w-xs" 
            value={streamValue}
            onSelectionChange={onStreamSelect}
        >
            <SelectItem key='1' value='1'>Agriculture</SelectItem>
            <SelectItem key='2' value='2'>Gender</SelectItem>
            <SelectItem key='3' value='3'>Climate Finance</SelectItem>
            <SelectItem key='4' value='4'>Adaptation</SelectItem>
            <SelectItem key='5' value='5'>IPCC</SelectItem>
        </Select>
        
        {streamValue && (
          <div className="text-right">
            <p className="text-sm font-bold">{filteredItems.length} {streamNames[streamValue as keyof typeof streamNames] || 'Climate'} Documents</p>          </div>
        )}
      </div>
      
      <div className="mt-5">
        <Input
          isClearable
          classNames={{
            base: "w-full sm:max-w-[44%]",
            inputWrapper: "border-1",
            input: ["fontsmall"],
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
}, [filterValue, streamValue, onSearchChange, onStreamSelect, filteredItems.length]);


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
    case "number":
      const currentIndex = items.findIndex(item => item === article);
      return (
        <div className="flex flex-col">
          <p className="text-bold text-sm">{currentIndex + 1 + (page - 1) * rowsPerPage}</p>
        </div>
      );
      case "name":
        return (
          <div className="flex flex-col">
            <Accordion isCompact defaultExpandedKeys={["item"]} itemClasses={itemClasses}>
              <AccordionItem key="item" title={article.name} className="fontsmall">
                {article.condensed_summary}
              </AccordionItem>
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
              href={"/article_detail/"+article.id}
              as={Link}
            >
              View Detail
            </Button>
            <Button 
            color="primary" 
            size="sm" 
            onClick={() => window.open(article.url, '_blank')}
            variant="solid"
          >
            Visit
          </Button>
          </div>
        );
      default:
        return cellValue;
    }
  }, [items, page, rowsPerPage]);

  return (
    <Container className="light">
      <Row className="mt-6">
        <Col className="md-6">
          <Table 
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