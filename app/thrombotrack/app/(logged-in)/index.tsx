// Home screen (list of oxygenators and relevant info)

import {
  TextInput,
  View,
  StyleSheet,
  FlatList,
  Text,
  TouchableOpacity,
  ActivityIndicator,
} from "react-native";
import { FC, JSX, useEffect, useState } from "react";
import Entypo from "@expo/vector-icons/Entypo";
import { Oxygenator, OxygenatorType } from "@/constants/types";
import { apiFetch } from "@/api";
import { loadThumbnails } from "@/helpers";
import OxygenatorCard from "@/components/OxygenatorCard";
import * as Colors from "@/constants/colors";

const HomeScreen: FC = (): JSX.Element => {
  const [oxygenators, setOxygenators] = useState<Oxygenator[]>([]); // list of all oxygenators
  const [filteredOxygenators, setFilteredOxygenators] = useState<Oxygenator[]>(
    [],
  ); // filtered oxygenators by search input
  const [isLoading, setIsLoading] = useState<boolean>(true); // display loading indicator
  const [search, setSearch] = useState<string>(""); // current search input

  /**
   * Gets the current list of oxygenators.
   */
  useEffect(() => {
    apiFetch("/oxygenators")
      .then((oxygenators: Required<Oxygenator>[]) => {
        setOxygenators(
          oxygenators.map((o) => ({
            ...o,
            thumbnail: null, // temporarily set to null while loadThumbnails loads the blobs
          })),
        );
        loadThumbnails(oxygenators, setOxygenators);
      })
      .catch((error) => console.error(error))
      .finally(() => setIsLoading(false));
  }, []);

  /**
   * Filters the list of oxygenators by the search input.
   */
  useEffect(() => {
    setFilteredOxygenators(
      oxygenators.filter((oxygenator) =>
        oxygenator.name.toLowerCase().includes(search.toLowerCase()),
      ),
    );
  }, [oxygenators, search]);

  /**
   * Creates a new oxygenator.
   *
   * Update `oxygenators` to include the added oxygenator in sorted order.
   */
  const createOxygenator = (name: string): void => {
    apiFetch("/oxygenators", {
      method: "POST",
      body: {
        name,
      },
    })
      .then((data: Oxygenator) => {
        setOxygenators(
          [
            ...oxygenators.filter((oxygenator) => oxygenator.id !== undefined),
            data,
          ].sort((a, b) => a.name.localeCompare(b.name)),
        );
        setIsLoading(false);
      })
      .catch((error) => {
        console.error(error);
      });
  };

  /**
   * Edits an oxygenator name or type.
   *
   * @param oxygenatorId ID of oxygenator to edit
   * @param payload New name and/or type
   */
  const editOxygenator = (
    oxygenatorId: string,
    payload: Pick<Partial<Oxygenator>, "name" | "type">,
  ): void => {
    apiFetch(`/oxygenators/${oxygenatorId}`, {
      method: "PATCH",
      body: payload,
    })
      .then(() => {
        setOxygenators(
          oxygenators.map((oxygenator) => {
            if (oxygenator.id === oxygenatorId) {
              return {
                ...oxygenator,
                ...payload,
              };
            } else {
              return oxygenator;
            }
          }),
        );
      })
      .catch((error) => {
        console.error(error);
      });
  };

  /**
   * Deletes an oxygenator.
   *
   * @param oxygenatorId ID of oxygenator to delete. Undefined ID means to abandon the oxygenator
   *                     currently being added.
   */
  const deleteOxygenator = (oxygenatorId?: string): void => {
    if (oxygenatorId === undefined) {
      setOxygenators(
        oxygenators.filter((oxygenator) => oxygenator.id !== oxygenatorId),
      );
      return;
    }

    apiFetch(`/oxygenators/${oxygenatorId}`, {
      method: "DELETE",
    })
      .then(() => {
        setOxygenators(
          oxygenators.filter((oxygenator) => oxygenator.id !== oxygenatorId),
        );
      })
      .catch((error) => {
        console.error(error);
      });
  };

  const renderListEmpty = () => (
    <View>
      <Text style={styles.centeredText}>No oxygenators found.</Text>
      <Text style={styles.centeredText}>
        Use the &quot;+&quot; button to add a new oxygenator.
      </Text>
    </View>
  );

  const renderDivider = () => <View style={styles.divider} />;

  const renderItem = ({ item }: { item: Oxygenator }): JSX.Element => (
    <OxygenatorCard
      oxygenator={item}
      createOxygenator={createOxygenator}
      editOxygenator={editOxygenator}
      deleteOxygenator={deleteOxygenator}
    />
  );

  const doPressAdd = () => {
    setOxygenators([
      {
        name: "",
        type: OxygenatorType.NAUTILUS,
        thumbnail: null,
        clot_area: null,
        fibrin_area: null,
        imaged_at: null,
        annotated_by: null,
      },
      ...oxygenators,
    ]);
  };

  return (
    <View style={styles.container}>
      {isLoading ? (
        <ActivityIndicator color={Colors.PURPLE} size="large" />
      ) : (
        <View>
          {oxygenators.length > 0 ? (
            <TextInput
              onChangeText={setSearch}
              placeholder="Search..."
              placeholderTextColor={Colors.GRAY}
              style={styles.search}
            />
          ) : null}

          <TouchableOpacity style={styles.addButton} onPress={doPressAdd}>
            <Entypo name="plus" size={18} color={Colors.PURPLE} />
            <Text style={styles.addText}>Add oxygenator</Text>
          </TouchableOpacity>

          <FlatList
            ItemSeparatorComponent={renderDivider}
            ListEmptyComponent={renderListEmpty}
            keyExtractor={(item) => item.id ?? "unsaved"}
            data={filteredOxygenators}
            renderItem={renderItem}
          />
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: 10,
  },
  search: {
    backgroundColor: Colors.WHITE,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: `${Colors.BLACK}1a`,
    marginBottom: 10,
    fontSize: 14,
    padding: 10,
  },
  centeredText: {
    textAlign: "center",
  },
  addButton: {
    height: 50,
    marginBottom: 10,
    borderColor: Colors.PURPLE,
    backgroundColor: `${Colors.PURPLE}1a`,
    borderWidth: 1,
    borderRadius: 15,
    display: "flex",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 5,
  },
  addText: {
    fontWeight: 600,
    color: Colors.PURPLE,
  },
  divider: {
    height: 1,
    backgroundColor: Colors.GRAY_5,
    marginHorizontal: 16,
    marginVertical: 10,
  },
});

export default HomeScreen;
